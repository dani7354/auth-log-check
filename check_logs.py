#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from datetime import datetime
from records import LoginAttempt, Connection
import os
import re
import sys

FAILED_LOGIN_INVALID_KEY = 0
FAILED_LOGIN_INVALID_USER = 1
NEW_CONNECTION = 2

LOGIN_ATTEMPT = "login_attempt"
CONNECTION = "connection"
CSV_DELIMITER = ";"

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10,
          "nov": 11, "dec": 12}

key_to_typename = {
    FAILED_LOGIN_INVALID_KEY: LOGIN_ATTEMPT,
    FAILED_LOGIN_INVALID_USER: LOGIN_ATTEMPT,
    NEW_CONNECTION: CONNECTION
}

regular_expressions = {
    FAILED_LOGIN_INVALID_KEY: "^\w{3}\s{1,2}\d{1,2} \d{2}:\d{2}:\d{2} pi-nas sshd\[\d+\]: Failed publickey.+$",
    FAILED_LOGIN_INVALID_USER: "^\w{3}\s{1,2}\d{1,2} \d{2}:\d{2}:\d{2} pi-nas sshd\[\d+\]: Invalid user.+$",
    NEW_CONNECTION: "^\w{3}\s{1,2}\d{1,2} \d{2}:\d{2}:\d{2} pi-nas sshd\[\d+\]: Connection from.+$"
}

output_filenames = {
    FAILED_LOGIN_INVALID_KEY: "login_attempts.csv",
    FAILED_LOGIN_INVALID_USER: "login_attempts.csv",
    NEW_CONNECTION: "connections.csv"
}

line_parsing_func = {}


def add_parsing_functions():
    line_parsing_func[FAILED_LOGIN_INVALID_KEY] = parse_login_invalid_key
    line_parsing_func[FAILED_LOGIN_INVALID_USER] = parse_login_invalid_user
    line_parsing_func[NEW_CONNECTION] = parse_new_connection


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output-dir", dest="output_dir", required=True)
    parser.add_argument("-l", "--logs", dest="log_files", nargs="+", type=FileType("r"), required=True)
    return parser.parse_args()


def create_regex_patterns():
    regex_patterns = []
    for key, value in regular_expressions.items():
        pattern = re.compile(value)
        regex_patterns.append((key, pattern))

    return regex_patterns


def line_is_match(line, regex_patterns):
    for pattern in regex_patterns:
        if pattern[1].match(line):
            return True, pattern[0]

    return False, None


def read_log(log, regex_patterns):
    matches = []
    for line in log:
        result = line_is_match(line, regex_patterns)
        if result[0]:
            matches.append((result[1], line))

    return matches


def parse_field(line, substr_before, substr_after):
    start_index = line.find(substr_before) + len(substr_before)
    end_index = line.find(substr_after, start_index)

    return line[start_index:end_index].strip()


def parse_ip(line):
    substr_before_value = "from "
    substr_after_value = " "

    return parse_field(line, substr_before_value, substr_after_value)


def parse_username_invalid_key(line):
    substr_before_value = "for "
    substr_after_value = " "

    return parse_field(line, substr_before_value, substr_after_value)


def parse_invalid_username(line):
    substr_before_value = "user "
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
    date_split = [x.strip() for x in date.split(" ")]

    if len(date_split) == str_split_count_padded:
        day_no = f"0{date_split[2]}"
    else:
        day_no = date_split[1]

    month_no = MONTHS[date_split[0].lower()]

    if month_no > today.month:
        year_no = today.year - 1
    else:
        year_no = today.year

    return f"{year_no}-{month_no}-{day_no} {date_split[-1]}"


def parse_login_invalid_key(line):
    ip = parse_ip(line)
    user = parse_username_invalid_key(line)
    port = parse_port(line)
    date = parse_date(line)

    return LoginAttempt(user, ip, port, date)


def parse_login_invalid_user(line):
    ip = parse_ip(line)
    user = parse_invalid_username(line)
    port = parse_port(line)
    date = parse_date(line)

    return LoginAttempt(user, ip, port, date)


def parse_new_connection(line):
    ip = parse_ip(line)
    port = parse_port(line)
    date = parse_date(line)

    return Connection(ip, port, date)


def parse_matched_lines(matches):
    parsed_matches = []
    for match in matches:
        type_key = match[0]
        line = match[1]
        parsing_function = line_parsing_func[type_key]
        parsed_match = parsing_function(line)
        parsed_matches.append((type_key, parsed_match))

    return parsed_matches


def create_record(csv_record, key):
    typename = key_to_typename[key]
    if typename == "connection":
        return Connection.create_from_csv_record(csv_record)
    elif typename == "login_attempt":
        return LoginAttempt.create_from_csv_record(csv_record)

    raise Exception("Record type not implemented!")


def get_records_by_type(matched_records):
    records_by_type = {}
    for record in matched_records:
        type_key = record[0]
        if type_key not in records_by_type:
            records_by_type[type_key] = []
        records_by_type[type_key].append(record)

    return records_by_type


def exclude_existing_records_from_file(new_records, output_file, key):
    if not os.path.isfile(output_file):
        return

    new_records_dct = {a[1].id: a for a in new_records}
    existing_records_dct = {}
    with open(output_file, "r") as output_file:
        lines = output_file.readlines()[1:]

    for line in lines:
        record = create_record(line, key)
        existing_records_dct[record.id] = record

    for key in existing_records_dct.keys():
        if key in new_records_dct:
            new_records.remove(new_records_dct[key])


def exclude_existing_records(new_records, output_dir):
    records_by_type = get_records_by_type(new_records)
    for key, records in records_by_type.items():
        filename = output_filenames[key]
        exclude_existing_records_from_file(records, os.path.join(output_dir, filename), key)

    return records_by_type


def write_to_file(file, records):
    if not os.path.isfile(file):
        with open(file, "w") as output_file:
            output_file.write(f"{records[0][1].create_csv_header_row(CSV_DELIMITER)}\n")

    with open(file, "a") as output_file:
        for record in records:
            line = record[1].create_csv_record()
            output_file.write(f"{line}\n")


def main():
    try:
        print("Starting check...")

        print("Parsing arguments...")
        arguments = parse_arguments()
        add_parsing_functions()

        print("Reading regular expressions...")
        regex_patterns = create_regex_patterns()

        error_count = 0
        file_counter = 0
        total_files = len(arguments.log_files)
        new_matches = []
        for log in arguments.log_files:
            try:
                file_counter += 1
                base_log_string = f"File {file_counter} of {total_files}"

                print(f"{base_log_string}: Reading log file: {log.name}...")
                matches = read_log(log, regex_patterns)
                print(f"{base_log_string}: Found {len(matches)} matches!")

                print(f"{base_log_string}: Parsing matching lines...")
                parsed_matches = parse_matched_lines(matches)

                new_matches.extend(parsed_matches)
                print(f"{base_log_string}: Done!")

            except Exception as ex:
                print(f"Error while reading file {log}... {ex}")
                error_count += 1

        print("Excluding existing rows from results...")
        new_records_by_type = exclude_existing_records(new_matches, arguments.output_dir)
        for type_key, records in new_records_by_type.items():
            output_file = os.path.join(arguments.output_dir, output_filenames[type_key])

            print(f"Writing to {output_file}...")
            write_to_file(output_file, records)

        if error_count == 0:
            print("Done!")
            sys.exit(0)
        else:
            print(f"Finished with {error_count} errors!")
            sys.exit(1)

    except Exception as ex:
        print(f"Something went wrong: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    main()
