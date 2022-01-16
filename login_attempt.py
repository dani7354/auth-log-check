from hashlib import sha256

DEFAULT_CSV_DELIMITER = ";"

def get_csv_header_row(delimiter=DEFAULT_CSV_DELIMITER):
    return f"id{delimiter}user{delimiter}src_ip{delimiter}src_port{delimiter}date"


def create_csv_record(attempt):
    return f"{attempt.id};{attempt.user};{attempt.src_ip};{attempt.src_port};{attempt.datetime}"


def create_from_csv_record(record, delimiter=DEFAULT_CSV_DELIMITER):
    record_split = record.split(delimiter)
    return LoginAttempt(record_split[1],
        record_split[2],
        record_split[3],
        record_split[4],
        record_split[0])


class LoginAttempt(object):
    def _generate_id(self):
        input_str = f"{self.user}{self.src_ip}{self.src_port}{self.datetime}"
        return sha256(input_str.encode("ascii")).hexdigest()


    def __init__(self, user, src_ip, src_port, datetime, id = None):
        self.user = user
        self.src_ip = src_ip
        self.src_port = src_port
        self.datetime = datetime
        self.id = id if not id is None else self._generate_id()
