import json
import os


class Configuration:

    def __init__(self):
        self.mail = {
            "host": "sample.mail.host",
            "port": 465,
            "user": "sample",
            "password": "sample",
            "use_ssl": True,
            "use_tls": False
        }
        self.mysql = {
            "host": "127.0.0.1",
            "user": "root",
            "password": "root",
            "database": "allec"
        }

    def load_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError()

        with open(file_path) as json_file:
            data = json.load(json_file)

            self.mail = data['mail']
            self.mysql = data['mysql']
