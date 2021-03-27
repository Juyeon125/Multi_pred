import os

DEBUG = True
ENV = "production" if not DEBUG else "development"
SECRET_KEY = os.urandom(12).hex() if not DEBUG else "DEV"

MAIL = {
    "host": "sample.mail.host",
    "port": 465,
    "user": "sample",
    "password": "sample",
    "use_ssl": True,
    "use_tls": False,
}
DB = {
    "host": "127.0.0.1",
    "user": "allec",
    "password": "allec",
    "database": "allec"
}
