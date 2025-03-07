# Zoom Reports Cleaner

Zoom reports, which report attendance at Zoom meetings, sometimes omit the email address of select participants, even when authentication to attend the meeting is required. This project attempts to rectify that by copying email addresses from a separate roster CSV file that includes the email addresses to the Zoom record CSV files. All changes are logged to a log file.

This assumes you have a roster file of some kind. For example, if you are teaching an online course, you may have a student roster that includes all student names and email addresses.

## Usage

1. Place the Zoom record CSV files in the `reports` directory.
1. Place the roster CSV file in the `rosters` directory.
1. Install dependencies (this is easiest done by using `pipenv shell` and `pipenv install`) (install `pipenv` with `pip install pipenv`) if you don't already have it.
1. Run the script with `python main.py` or `python3 main.py`.

## Conventions

- report file names must have a two-letter prefix that matches the prefix in the corresponding roster file name.
- report files are assumed to have "`Name (original name)`", and "`Email`" fields.
- roster files are assumed to have "`Last`", "`First`", and "`Email`" fields.

## Configuration

Default configuration is in the `config.yml` file. It is possible to change some of the details there to suit your own report and roster CSV file structures and your preferred directory structure for reports, rosters, and logs.
