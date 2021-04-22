import os


class LocalLevelConfig:
    ENV = "development"
    DEBUG = True
    SECRET_KEY = "ce7ea57bcec4ea045191c43a"


class ProductionLevelConfig:
    ENV = "production"
    DEBUG = False
    SECRET_KEY = "5ae9fc9c349602a1111ef1d4"
