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
    roster files are assumed to have "Last" (or "Last name"), "First" (or "First name"), and "Email" (or "Email address") fields; other fields are ignored.

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
import difflib

# convert YAML to dictionary
# Load YAML from the file named config.yml
with open("config.yml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

# extract settings from config
reports_dir = config["REPORTS_DIR"]
rosters_dir = config["ROSTERS_DIR"]
logs_dir = config["LOGS_DIR"]
REPORT_NAME_FIELD = config["REPORT_NAME_FIELD"]
REPORT_EMAIL_FIELD = config["REPORT_EMAIL_FIELD"]

# roster fields may be a single column name or a list of acceptable alternate column names
def as_list(value):
    return value if isinstance(value, list) else [value]


ROSTER_FIELD_ALIASES = {
    "Last": as_list(config["ROSTER_LAST_NAME_FIELD"]),
    "First": as_list(config["ROSTER_FIRST_NAME_FIELD"]),
    "Email": as_list(config["ROSTER_EMAIL_FIELD"]),
}
# internal keys used for each roster row, regardless of the column names in the roster file
ROSTER_LAST_NAME_FIELD = "Last"
ROSTER_FIRST_NAME_FIELD = "First"
ROSTER_EMAIL_FIELD = "Email"
FILENAME_PREFIX_LENGTH = config["FILENAME_PREFIX_LENGTH"]
# minimum difflib similarity score (0 to 1) for a last-resort match on a misspelled name
FUZZY_MATCH_THRESHOLD = config.get("FUZZY_MATCH_THRESHOLD", 0.75)

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
    s = open(
        file_path, mode="r", encoding="utf-8-sig"
    ).read()  # read file in bom-agnostic mode
    open(file_path, mode="w", encoding="utf-8").write(
        s
    )  # write file in standard utf-8 mode


def get_email_from_roster(roster_file, student_zoom_name):
    """
    Retrieve the email address of a student from the roster file based on the student's full name.
    """

    # save all students in our roster
    student_roster = []
    # utf-8-sig handles rosters saved with a BOM
    with open(roster_file, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        # find which column holds each field we need, ignoring case and stray whitespace
        columns = {name.strip().lower(): name for name in reader.fieldnames or []}
        roster_columns = {}
        for field, aliases in ROSTER_FIELD_ALIASES.items():
            column = next((columns[a.lower()] for a in aliases if a.lower() in columns), None)
            if column is None:
                raise ValueError(
                    f"{roster_file} is missing a {field} column (expected one of: {', '.join(aliases)})"
                )
            roster_columns[field] = column
        # add each student to our roster list, keeping only the fields we need and ignoring any others
        for row in reader:
            student_roster.append(
                {field: (row[column] or "").strip() for field, column in roster_columns.items()}
            )

    # Remove any content in parentheses from the student_zoom_name
    student_full_name = re.sub(r"\s*\(.*?\)", "", student_zoom_name).strip()

    if not student_full_name:
        return None

    # split the name into first and last
    split_student_full_name = student_full_name.split(" ", 1)
    if len(split_student_full_name) >= 2:
        # we have both last and first name.. try to match both
        student_first_name, student_last_name = split_student_full_name

        for row in student_roster:
            # exact matches may fail due to some differences in name syntax, so trying 'in' operation instead
            # case-insensitive matching to handle differences in capitalization
            if (
                student_last_name.lower() in row[ROSTER_LAST_NAME_FIELD].lower()
                and student_first_name.lower() in row[ROSTER_FIRST_NAME_FIELD].lower()
            ):
                return row[ROSTER_EMAIL_FIELD]

        # as a backup, in case one of the names is spelled differently, look for a unique match on last name, then first name
        name_checks = [
            (student_last_name, ROSTER_LAST_NAME_FIELD),
            (student_first_name, ROSTER_FIRST_NAME_FIELD),
        ]
    else:
        # as a backup, look for only a partial match with first or last name
        student_name_token = split_student_full_name[0]
        name_checks = [
            (student_name_token, ROSTER_FIRST_NAME_FIELD),
            (student_name_token, ROSTER_LAST_NAME_FIELD),
        ]

    for student_name, roster_field in name_checks:
        # find all students with this name
        matching = [
            row
            for row in student_roster
            if student_name.lower() in row[roster_field].lower()
        ]
        if len(matching) == 1:
            # only return if one student matches the name
            return matching[0][ROSTER_EMAIL_FIELD]

    # as a last resort, look for a unique roster name that is similar enough to catch misspellings
    matching_similar = []
    for row in student_roster:
        roster_full_name = f"{row[ROSTER_FIRST_NAME_FIELD]} {row[ROSTER_LAST_NAME_FIELD]}".strip()
        # compare names as written, and with words sorted, in case the names are in a different order
        score = max(
            difflib.SequenceMatcher(None, student_name.lower(), roster_name.lower()).ratio()
            for student_name, roster_name in [
                (student_full_name, roster_full_name),
                (" ".join(sorted(student_full_name.split())), " ".join(sorted(roster_full_name.split()))),
            ]
        )
        if score > FUZZY_MATCH_THRESHOLD:
            matching_similar.append((row, roster_full_name, score))
    if len(matching_similar) == 1:
        # only return if one student is similar enough; log it so the match can be reviewed
        row, roster_full_name, score = matching_similar[0]
        with open(log_filename, mode="a", encoding="utf-8") as log_file:
            log_file.write(
                f"{datetime.now()} - {roster_file} - {student_zoom_name} - similar to {roster_full_name} (score {score:.2f})\n"
            )
        return row[ROSTER_EMAIL_FIELD]

    return None


def fill_missing_emails(report_file, roster_file):
    """
    Fill in missing email addresses in the report file using the corresponding roster file.
    Log the operations performed.
    """
    updated_rows = []
    # print(f"Processing {report_file} with {roster_file}")
    with open(report_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        # find the report's name and email columns, ignoring case and stray whitespace
        columns = {name.strip().lower(): name for name in fieldnames or []}
        name_field = columns.get(REPORT_NAME_FIELD.lower(), REPORT_NAME_FIELD)
        email_field = columns.get(REPORT_EMAIL_FIELD.lower(), REPORT_EMAIL_FIELD)
        for row in reader:
            # drop any extra or missing cells in malformed rows so they don't break the CSV writer
            # (don't re-encode values here... doing so garbles non-ASCII characters on every run)
            row = {
                key: value
                for key, value in row.items()
                if isinstance(value, str) and isinstance(key, str)
            }
            # print(f"row: {row}")

            if not row[email_field]:
                email = get_email_from_roster(roster_file, row[name_field])
                if email:
                    row[email_field] = email
                    with open(log_filename, mode="a", encoding="utf-8") as log_file:
                        log_file.write(
                            f"{datetime.now()} - {report_file} - {row[name_field]} - {email}\n"
                        )
                else:
                    with open(log_filename, mode="a", encoding="utf-8") as log_file:
                        log_file.write(
                            f"{datetime.now()} - {report_file} - {row[name_field]} - Email not found\n"
                        )
            updated_rows.append(row)

    with open(report_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)


def main():
    """
    Main function that processes all report files in the reports directory.
    Matches each report file with the corresponding roster file and fills in missing emails.
    """
    for report_filename in os.listdir(reports_dir):
        if report_filename.endswith(".csv"):
            report_file = os.path.join(reports_dir, report_filename)
            roster_file_prefix = report_filename[
                :FILENAME_PREFIX_LENGTH
            ]  # assume prefix in report and roster filename
            roster_file = os.path.join(
                rosters_dir, f"{roster_file_prefix}-roster.csv"
            )  # assume same prefix on roster filename
            if os.path.exists(roster_file):
                remove_bom_from_file(report_file)  # remove BOM if it exists
                fill_missing_emails(
                    report_file, roster_file
                )  # fill in missing email addresses from roster
            else:
                with open(log_filename, mode="a", encoding="utf-8") as log_file:
                    log_file.write(
                        f"{datetime.now()} - {report_file} - Roster file not found\n"
                    )


if __name__ == "__main__":
    # Run it
    main()
