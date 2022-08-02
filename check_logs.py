#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from records import LoginAttempt, Connection, Record
from email_notification import EmailNotificationService, EmailConfiguration
import parsing
import json
import os
import re
import sys


FAILED_LOGIN_INVALID_KEY = 0
FAILED_LOGIN_INVALID_USER = 1
NEW_CONNECTION = 2

LOGIN_ATTEMPT = "login_attempt"
CONNECTION = "connection"
CSV_DELIMITER = ";"

# for mail configuration
SMTP_HOST = "smtp_host"
SMTP_PORT = "smtp_port"
SMTP_USER = "smtp_user"
SMTP_PASSWORD = "smtp_password"
MAIL_RECIPIENT = "mail_recipient"
MAIL_SENDER = "mail_sender"


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


def add_parsing_functions() -> None:
    line_parsing_func[FAILED_LOGIN_INVALID_KEY] = parse_login_invalid_key
    line_parsing_func[FAILED_LOGIN_INVALID_USER] = parse_login_invalid_user
    line_parsing_func[NEW_CONNECTION] = parse_new_connection


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output-dir", dest="output_dir", required=True)
    parser.add_argument("-l", "--logs", dest="log_files", nargs="+", type=FileType("r"), required=True)
    parser.add_argument("-ec", "--email-config", dest="email_config", type=FileType("r"), required=False)

    return parser.parse_args()


def create_regex_patterns() -> list:
    regex_patterns = []
    for key, value in regular_expressions.items():
        pattern = re.compile(value)
        regex_patterns.append((key, pattern))

    return regex_patterns


def line_is_match(line, regex_patterns) -> tuple:
    for pattern in regex_patterns:
        if pattern[1].match(line):
            return True, pattern[0]

    return False, None


def read_log(log, regex_patterns) -> list:
    matches = []
    for line in log:
        result = line_is_match(line, regex_patterns)
        if result[0]:
            matches.append((result[1], line))

    return matches


def parse_login_invalid_key(line) -> LoginAttempt:
    ip = parsing.parse_ip(line)
    user = parsing.parse_username_invalid_key(line)
    port = parsing.parse_port(line)
    date = parsing.parse_date(line)

    return LoginAttempt(user, ip, port, date)


def parse_login_invalid_user(line) -> LoginAttempt:
    ip = parsing.parse_ip(line)
    user = parsing.parse_invalid_username(line)
    port = parsing.parse_port(line)
    date = parsing.parse_date(line)

    return LoginAttempt(user, ip, port, date)


def parse_new_connection(line) -> Connection:
    ip = parsing.parse_ip(line)
    port = parsing.parse_port(line)
    date = parsing.parse_date(line)

    return Connection(ip, port, date)


def parse_matched_lines(matches) -> list:
    parsed_matches = []
    for match in matches:
        type_key = match[0]
        line = match[1]
        parsing_function = line_parsing_func[type_key]
        parsed_match = parsing_function(line)
        parsed_matches.append((type_key, parsed_match))

    return parsed_matches


def create_record(csv_record, key) -> Record:
    typename = key_to_typename[key]
    if typename == CONNECTION:
        return Connection.create_from_csv_record(csv_record)
    elif typename == LOGIN_ATTEMPT:
        return LoginAttempt.create_from_csv_record(csv_record)

    raise Exception("Record type not implemented!")


def get_records_by_type(matched_records) -> dict:
    records_by_type = {}
    for record in matched_records:
        type_key = record[0]
        if type_key not in records_by_type:
            records_by_type[type_key] = []
        records_by_type[type_key].append(record)

    return records_by_type


def exclude_existing_records_from_file(new_records, output_file, key) -> None:
    if not os.path.isfile(output_file):
        return

    new_records_dct = {a[1].id: a for a in new_records}
    existing_records_dct = {}
    with open(output_file, "r") as output_file:
        lines = output_file.readlines()[1:]

    for line in lines:
        record = create_record(line, key)
        existing_records_dct[record.id] = record

    for key in new_records_dct.keys():
        if key in existing_records_dct:
            new_records.remove(new_records_dct[key])


def exclude_existing_records(new_records, output_dir) -> dict:
    records_by_type = get_records_by_type(new_records)
    new_records = {}
    for key, records in records_by_type.items():
        filename = output_filenames[key]
        exclude_existing_records_from_file(records, os.path.join(output_dir, filename), key)

        if len(records) > 0:
            new_records[key] = records

    return new_records


def write_to_file(file, records) -> None:
    if not os.path.isfile(file):
        with open(file, "w") as output_file:
            output_file.write(f"{records[0][1].create_csv_header_row(CSV_DELIMITER)}\n")

    with open(file, "a") as output_file:
        for record in records:
            line = record[1].create_csv_record()
            output_file.write(f"{line}\n")


def get_config_from_json(path) -> dict:
    return json.load(path)


def load_email_config(path) -> EmailConfiguration:
    config_data = get_config_from_json(path)
    if not {SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_SENDER, MAIL_RECIPIENT} <= config_data.keys():
        raise Exception("Missing properties in config file!")

    host = config_data[SMTP_HOST]
    port = config_data[SMTP_PORT]
    user = config_data[SMTP_USER]
    password = config_data[SMTP_PASSWORD]
    sender = config_data[MAIL_SENDER]
    recipient = config_data[MAIL_RECIPIENT]

    return EmailConfiguration(host, port, user, password, sender, recipient)


def send_email_notification(new_records, email_configuration) -> None:
    email_service = EmailNotificationService(email_configuration)
    email_service.send_email_notification(new_records)


def main() -> None:
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

        if len(new_records_by_type) == 0:
            print("No rows to write...")
            sys.exit(0)

        for type_key, records in new_records_by_type.items():
            output_file = os.path.join(arguments.output_dir, output_filenames[type_key])

            print(f"Writing to {output_file}...")
            write_to_file(output_file, records)

        if arguments.email_config:
            print(f"Sending notification email...")
            email_configuration = load_email_config(arguments.email_config)
            send_email_notification(new_records_by_type, email_configuration)
            print("Email sent")

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
