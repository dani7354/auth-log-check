from hashlib import sha256

def create_csv_record(attempt):
    return f"{attempt.id};{attempt.user};{attempt.src_ip};{attempt.src_port};{attempt.datetime}"

def create_from_csv_record(record, delimiter=";"):
    record_split = record.split(delimiter)
    return LoginAttempt(record_split[1],
        record_split[2],
        record_split[3],
        record_split[4])

class LoginAttempt(object):
    def _generate_id(self):
        input_str = f"{self.user}{self.src_ip}{self.src_port}{self.datetime}"
        return sha256(input_str.encode("ascii")).hexdigest()

    def __init__(self, user, src_ip, src_port, datetime):
        self.user = user
        self.src_ip = src_ip
        self.src_port = src_port
        self.datetime = datetime
        self.id = self._generate_id()
