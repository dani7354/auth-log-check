#!/usr/bin/env python3
from argparse import ArgumentParser
from login_attempt import LoginAttempt, create_from_csv_record, create_csv_record
import pathlib
import re

FAILED_LOGIN = 0

line_parsing_func = { }


def add_parsing_functions():
    line_parsing_func[FAILED_LOGIN] = parse_failed_login


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("-o", "--output", dest="output_file",type=str, required=True)
    parser.add_argument("-l", "--logs", dest="log_files", type=open, nargs="+", required=True)
    return parser.parse_args()


def read_regex_patterns(file):
    delimiter = ";"
    regex_patterns = []
    with open(file, "r") as regex_file:
        for line in regex_file:
            line_split = line.split(delimiter)
            pattern = re.compile(line_split[0])
            regex_patterns.append((pattern, line_split[1]))

    return regex_patterns


def line_is_match(line, regex_patterns):
    for pattern in regex_patterns:
        if pattern[0].match(line):
            return True, pattern[1]

    return False, None


def read_log(log_file, regex_patterns):
    matches = []
    with open(log_file, "r") as log:
        for line in log:
            result = line_is_match(line, regex_patterns)
            if result[0]:
                matches.append((line, result[1]))

    return matches


def parse_field(line, substr_before, substr_after):
    start_index = line.find(substr_before) + len(substr_before)
    end_index = line.find(substr_after, start_index)

    return line[start_index, end_index].strip()


def parse_ip(line):
    substr_before_value = "from "
    substr_after_value = " "

    return parse_field(line, substr_before_value, substr_after_value)


def parse_user(line):
    substr_before_value = "for "
    substr_after_value = " "

    return parse_field(substr_before_value, substr_after_value)


def parse_port(line):
    substr_before_value = "port "
    substr_after_value = " "

    return parse_field(substr_before_value, substr_after_value)


def parse_date(line):
    start_index = 0
    end_index = 14

    return line[start_index:end_index].strip()


def parse_failed_login(line):
    ip = parse_ip(line)
    user = parse_user(line)
    port = parse_port(line)
    date = parse_date(line)

    return LoginAttempt(user, ip, port, date)


def parse_matched_lines(matches):
    for match in matches:
            parsing_function = line_parsing_func[match[1]]
            parsing_function(match[0])


def main():
    try:
        arguments = parse_arguments()
    except Exception as ex:
        print(f"Something went wrong: {ex}")


if __name__ == "__main__":
    main()
