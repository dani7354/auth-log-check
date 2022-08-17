from datetime import datetime

MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10,
          "nov": 11, "dec": 12}


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
