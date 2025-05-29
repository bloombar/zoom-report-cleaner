#!/usr/bin/env python3

"""
Fixes Zoom's CSV report files to fill in missing email addresses using data from separate roster files.
It logs the operations performed, including successful email retrievals and any errors encountered.

Directories:
    reports_dir: Directory containing the report files.
    rosters_dir: Directory containing the roster files.
    logs_dir: Directory where log files are written.

Conventions:
    config.yml contains conventions that can be modified:
    report file names area assumed to have a two-letter prefix that matches the prefix in the corresponding roster file name.
    report files are assumed to have "Name (original name)", and "Email" fields.
    roster files are assumed to have "Last", "First", and "Email" fields.

Usage:
    place roster files in the rosters directory
    place report files in the reports directory
    install dependencies (preferably using 'pipenv shell' and 'pipenv install')
    run the program!
"""


import os
import csv
from datetime import datetime
import yaml
import re

# convert YAML to dictionary
# Load YAML from the file named config.yml
with open('config.yml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# extract settings from config
reports_dir = config['REPORTS_DIR']
rosters_dir = config['ROSTERS_DIR']
logs_dir = config['LOGS_DIR']
REPORT_NAME_FIELD = config['REPORT_NAME_FIELD']
REPORT_EMAIL_FIELD = config['REPORT_EMAIL_FIELD']
ROSTER_LAST_NAME_FIELD = config['ROSTER_LAST_NAME_FIELD']
ROSTER_FIRST_NAME_FIELD = config['ROSTER_FIRST_NAME_FIELD']
ROSTER_EMAIL_FIELD = config['ROSTER_EMAIL_FIELD']
FILENAME_PREFIX_LENGTH = config['FILENAME_PREFIX_LENGTH']

# Ensure logs directory exists
os.makedirs(logs_dir, exist_ok=True)

# Create a log file with the current date
log_filename = os.path.join(logs_dir, f'log-{datetime.now().strftime("%Y%m%d")}.txt')

def remove_bom_from_file(file_path):
    """
    Remove the BOM (Byte Order Mark) from a file if it exists.
    This is necessary for CSV files that may have been saved with a BOM.
    """
    # Loop each file solving the problem - It will overwrite the original file
    s = open(file_path, mode='r', encoding='utf-8-sig').read() # read file in bom-agnostic mode
    open(file_path, mode='w', encoding='utf-8').write(s) # write file in standard utf-8 mode

def get_email_from_roster(roster_file, student_full_name):
    """
    Retrieve the email address of a student from the roster file based on the student's full name.
    """
    # Remove any content in parentheses from the student_full_name
    student_full_name = re.sub(r'\s*\(.*?\)', '', student_full_name).strip()

    # split the name into first and last
    split_student_full_name = student_full_name.split(' ', 1)
    if len(split_student_full_name) < 2:
        # if missing data, skip this row
        return None
    
    # we have data so continue
    student_first_name, student_last_name = split_student_full_name
    with open(roster_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # exact matches may fail due to some differences in name syntax, so trying 'in' operation instead
            if student_last_name in row[ROSTER_LAST_NAME_FIELD] and student_first_name in row[ROSTER_FIRST_NAME_FIELD]:
                return row[ROSTER_EMAIL_FIELD]
    return None

def fill_missing_emails(report_file, roster_file):
    """
    Fill in missing email addresses in the report file using the corresponding roster file.
    Log the operations performed.
    """
    updated_rows = []
    # print(f"Processing {report_file} with {roster_file}")
    with open(report_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            row = {key.encode('utf-8').decode('unicode_escape'): value.encode('utf-8').decode('unicode_escape') for key, value in row.items()}
            # print(f"row: {row}")

            if not row[REPORT_EMAIL_FIELD]:
                email = get_email_from_roster(roster_file, row[REPORT_NAME_FIELD])
                if email:
                    row[REPORT_EMAIL_FIELD] = email
                    with open(log_filename, mode='a', encoding='utf-8') as log_file:
                        log_file.write(f"{datetime.now()} - {report_file} - {row[REPORT_NAME_FIELD]} - {email}\n")
                else:
                    with open(log_filename, mode='a', encoding='utf-8') as log_file:
                        log_file.write(f"{datetime.now()} - {report_file} - {row[REPORT_NAME_FIELD]} - Email not found\n")
            updated_rows.append(row)
    
    with open(report_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

def main():
    """
    Main function that processes all report files in the reports directory.
    Matches each report file with the corresponding roster file and fills in missing emails.
    """
    for report_filename in os.listdir(reports_dir):
        if report_filename.endswith('.csv'):
            report_file = os.path.join(reports_dir, report_filename)
            roster_file_prefix = report_filename[:FILENAME_PREFIX_LENGTH] # assume prefix in report and roster filename
            roster_file = os.path.join(rosters_dir, f"{roster_file_prefix}-roster.csv") # assume same prefix on roster filename
            if os.path.exists(roster_file):
                remove_bom_from_file(report_file) # remove BOM if it exists
                fill_missing_emails(report_file, roster_file) # fill in missing email addresses from roster
            else:
                with open(log_filename, mode='a', encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.now()} - {report_file} - Roster file not found\n")

if __name__ == "__main__":
    # Run it
    main()