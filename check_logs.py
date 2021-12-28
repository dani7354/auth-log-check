#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from datetime import datetime
from login_attempt import LoginAttempt, create_from_csv_record, create_csv_record
import os
import re
import sys

FAILED_LOGIN = 0
CONNECTION = 1

MONTHS = {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12 }

regular_expressions = {
    FAILED_LOGIN: "^\w{3}\s{1,2}\d{1,2} \d{2}:\d{2}:\d{2} pi-nas sshd\[\d+\]: Failed publickey.+$"
}
line_parsing_func = { }


def add_parsing_functions():
    line_parsing_func[FAILED_LOGIN] = parse_failed_login


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", dest="output_file", required=True)
    parser.add_argument("-l", "--logs", dest="log_files", nargs="+", type=FileType("r"), required=True)
    return parser.parse_args()


def create_regex_patterns():
    global regular_expressions
    regex_patterns = []
    for key, value in regular_expressions.items():
        pattern = re.compile(value)
        regex_patterns.append((pattern, key))

    return regex_patterns


def line_is_match(line, regex_patterns):
    for pattern in regex_patterns:
        if pattern[0].match(line):
            return True, pattern[1]

    return False, None


def read_log(log, regex_patterns):
    matches = []
    for line in log:
        result = line_is_match(line, regex_patterns)
        if result[0]:
            matches.append((line, result[1]))

    return matches


def parse_field(line, substr_before, substr_after):
    start_index = line.find(substr_before) + len(substr_before)
    end_index = line.find(substr_after, start_index)

    return line[start_index:end_index].strip()


def parse_ip(line):
    substr_before_value = "from "
    substr_after_value = " "

    return parse_field(line, substr_before_value, substr_after_value)


def parse_user(line):
    substr_before_value = "for "
    substr_after_value = " "

    return parse_field(line, substr_before_value, substr_after_value)


def parse_port(line):
    substr_before_value = "port "
    substr_after_value = " "

    return parse_field(line, substr_before_value, substr_after_value)


def parse_date(line):
    start_index = 0
    end_index = 15
    str_split_count_padded = 4

    today = datetime.today()

    date = line[start_index:end_index].strip()
    date_splitted = [ x.strip() for x in date.split(' ') ]

    if len(date_splitted) == str_split_count_padded:
        day_no = f"0{date_splitted[2]}"
    else:
        day_no = date_splitted[1]

    month_no = MONTHS[date_splitted[0].lower()]

    if month_no > today.month:
        year_no = today.year - 1
    else:
        year_no = today.year

    return f"{year_no}-{month_no}-{day_no} {date_splitted[-1]}"





def parse_failed_login(line):
    ip = parse_ip(line)
    user = parse_user(line)
    port = parse_port(line)
    date = parse_date(line)

    return LoginAttempt(user, ip, port, date)


def parse_matched_lines(matches):
    login_attempts = []
    for match in matches:
        parsing_function = line_parsing_func[match[1]]
        login_attempt = parsing_function(match[0])
        login_attempts.append(login_attempt)

    return login_attempts


def write_to_file(file, login_attempts):
    with open(file, "a") as output_file:
        for login_attempt in login_attempts:
            line = create_csv_record(login_attempt)
            output_file.write(line + "\n")

def main():
    try:
        print("Starting check...")

        print("Parsing arguments...")
        arguments = parse_arguments()
        add_parsing_functions()

        print("Reading regular expressions...")
        regex_patterns = create_regex_patterns()

        file_counter = 0
        total_files = len(arguments.log_files)
        for log in arguments.log_files:
            file_counter += 1
            base_log_string = f"File {file_counter} of {total_files}"

            print(f"{base_log_string}: Reading log file: {log}...")
            matches = read_log(log, regex_patterns)
            print(f"{base_log_string}: Found {len(matches)} matches!")

            print(f"{base_log_string}: Parsing matching lines...")
            login_attempts = parse_matched_lines(matches)

            print(f"Writing to {arguments.output_file}...")
            write_to_file(arguments.output_file, login_attempts)

            print(f"{base_log_string}: Done!")

        print("Done!")
        sys.exit(0)

    except Exception as ex:
        print(f"Something went wrong: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
