#!/usr/bin/env python3

import os
import csv
from datetime import datetime

reports_dir = './reports'
rosters_dir = './rosters'
logs_dir = './logs'

# Ensure logs directory exists
os.makedirs(logs_dir, exist_ok=True)

# Create a log file with the current date
log_filename = os.path.join(logs_dir, f'log-{datetime.now().strftime("%Y%m%d")}.txt')

def get_email_from_roster(roster_file, student_full_name):
    student_first_name, student_last_name = student_full_name.split(' ', 1)
    with open(roster_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if student_last_name in row['Last'] and student_first_name in row['First']:
                return row['Email']
    return None

def fill_missing_emails(report_file, roster_file):
    updated_rows = []
    with open(report_file, mode='r') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        for row in reader:
            row = {key.encode('utf-8').decode('unicode_escape'): value for key, value in row.items()}
            if not row['Email']:
                email = get_email_from_roster(roster_file, row['Name (original name)'])
                if email:
                    row['Email'] = email
                    with open(log_filename, mode='a') as log_file:
                        log_file.write(f"{datetime.now()} - {report_file} - {row['Name (original name)']} - {email}\n")
                else:
                    with open(log_filename, mode='a') as log_file:
                        log_file.write(f"{datetime.now()} - {report_file} - {row['Name (original name)']} - Email not found\n")
            updated_rows.append(row)
    
    with open(report_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

def main():
    for report_filename in os.listdir(reports_dir):
        if report_filename.endswith('.csv'):
            report_file = os.path.join(reports_dir, report_filename)
            roster_file_prefix = report_filename[:2] # assume a two character prefix in report filename
            roster_file = os.path.join(rosters_dir, f"{roster_file_prefix}-roster.csv") # assume same prefix on roster filename
            if os.path.exists(roster_file):
                fill_missing_emails(report_file, roster_file)
            else:
                with open(log_filename, mode='a') as log_file:
                    log_file.write(f"{datetime.now()} - {report_file} - Roster file not found\n")

if __name__ == "__main__":
    main()