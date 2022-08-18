from hashlib import sha256

DEFAULT_CSV_DELIMITER = ";"


class Record:
    def __init__(self, src_ip, src_port, datetime, key):
        self.src_ip = src_ip
        self.src_port = src_port
        self.datetime = datetime
        self.id = key if key is not None else self._generate_id()

    def __eq__(self, other):
        if isinstance(other, Record):
            return self.id == other.id
        return False

    def __str__(self):
        return f"{self.get_type_name()} ID: {self.id} Date and time: {self.datetime} Source IP: {self.src_ip} Source port: {self.src_port}"

    def _generate_id(self):
        pass

    def create_csv_record(self):
        pass

    def create_csv_header_row(self):
        pass

    def get_type_name(self):
        return self.__class__.__name__


class Connection(Record):
    def _generate_id(self):
        input_str = f"{self.src_ip}{self.src_port}{self.datetime}"
        return sha256(input_str.encode("ascii")).hexdigest()

    def __init__(self, src_ip, src_port, datetime, key=None):
        super().__init__(src_ip, src_port, datetime, key)

    def create_csv_record(self, delimiter=DEFAULT_CSV_DELIMITER):
        return f"{self.id}{delimiter}{self.src_ip}{delimiter}{self.src_port}{delimiter}{self.datetime}"

    def create_csv_header_row(self, delimiter=DEFAULT_CSV_DELIMITER):
        return f"id{delimiter}src_ip{delimiter}src_port{delimiter}date"

    @staticmethod
    def create_from_csv_record(record, delimiter=DEFAULT_CSV_DELIMITER):
        record_split = record.split(delimiter)
        return Connection(record_split[1],
                          record_split[2],
                          record_split[3],
                          record_split[0])


class LoginAttempt(Record):
    def _generate_id(self):
        input_str = f"{self.user}{self.src_ip}{self.src_port}{self.datetime}"
        return sha256(input_str.encode("ascii")).hexdigest()

    def __init__(self, user, src_ip, src_port, datetime, key=None):
        self.user = user
        super().__init__(src_ip, src_port, datetime, key)

    def __str__(self):
        base_str = super().__str__()
        return f"{base_str} Username: {self.user}"

    def create_csv_record(self, delimiter=DEFAULT_CSV_DELIMITER):
        return f"{self.id}{delimiter}{self.user}{delimiter}{self.src_ip}{delimiter}{self.src_port}" \
               f"{delimiter}{self.datetime}"

    def create_csv_header_row(self, delimiter=DEFAULT_CSV_DELIMITER):
        return f"id{delimiter}user{delimiter}src_ip{delimiter}src_port{delimiter}date"

    @staticmethod
    def create_from_csv_record(record, delimiter=DEFAULT_CSV_DELIMITER):
        record_split = record.split(delimiter)
        return LoginAttempt(record_split[1],
                            record_split[2],
                            record_split[3],
                            record_split[4],
                            record_split[0])
