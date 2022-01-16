from hashlib import sha256


class Connection(object):
    def __init__(self, src_ip, src_port):
        self.src_ip = src_ip
        self.src_port = src_port

