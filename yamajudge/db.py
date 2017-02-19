from pymongo import MongoClient
import gridfs

from yamajudge.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='anubis', help='Database name.')


class Database(object):
    _instance = None

    def __new__(cls):
        if not cls._instance:
            client = MongoClient(options.options.db_host)
            cls._instance = client[options.options.db_name]
        return cls._instance


class Collection(object):
    _instances = {}

    def __new__(cls, name):
        if name not in cls._instances:
            cls._instances[name] = Database()[name]
        return cls._instances[name]


class GridFS(object):
    _instances = {}

    def __new__(cls, name):
        if name not in cls._instances:
            cls._instances[name] = gridfs.GridFS(Database(), name)
        return cls._instances[name]
