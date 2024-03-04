import json
import logging.config
import os
from pathlib import Path
from dotenv import load_dotenv

BASEDIR = Path(__file__).parent

if os.path.exists(BASEDIR / ".env"):
    load_dotenv()

DATA_PATH = BASEDIR / "data"

os.makedirs(DATA_PATH, exist_ok=True)

DETECT_LITE_DB = DATA_PATH / "db_detect.db"

SCUD_DB = {
    "drivername": "mssql+pyodbc",
    'host': "192.168.11.200",
    'database': "Orion15.11.2022",
    'username': "ASUP",
    'password': "qC4HptD",
    "query": {
        "driver": "ODBC Driver 17 for SQL Server",
        "TrustServerCertificate": "yes",
    },
}

DETECT_PG_DB = {
    "drivername": "postgresql+psycopg2",
    'host': "localhost",
    'database': "detect",
    'username': "postgres",
    'password': "Valm0nts89"
}

SOURCES = {
    '0': {
        'create': {
            'video_source': 0,
        },
        'start': {
            'unknown_save_step': 10,
            'width': 1024,
            'skipped_frames_coeff': 50,
            'faces_distance': 0.55,
            'intervals': []
        },
        'stream': {
            'is_record': False,
            'is_recognized': False
        }
    },
    '1': {
        'create': {
            'video_source': "rtsp://admin01:Epass1@192.168.9.15:554",
            'crop': (180, 480, 900, 2560)
        },
        'start': {
            'unknown_save_step': 10,
            'width': 1024,
            'skipped_frames_coeff': 50,
            'faces_distance': 0.6,
            'intervals': []
        },
        'stream': {
            'is_record': False,
            'is_recognized': False
        }
    },
    '2': {
        'create': {
            'video_source': r"D:\Records\Local Records\Ch1_192.168.9.13\_ (4).avi",
            'crop': (780, 1280, 980, 1860)
        },
        'start': {
            'unknown_save_step': 10,
            'width': 1024,
            'skipped_frames_coeff': 50,
            'faces_distance': 0.6,
            'intervals': []
        },
        'stream': {
            'is_record': False,
            'is_recognized': False
        }
    }
}

sources_settings = BASEDIR / "sources.json"

if os.path.exists(sources_settings):
    with open(sources_settings, 'r') as file:
        SOURCES = json.load(file)
else:
    with open(sources_settings, 'w') as file:
        json.dump(SOURCES, file)

LOG_QUEUE = []


class ListHandler(logging.Handler):
    def __init__(self, log_list):
        logging.Handler.__init__(self)
        self.log_list = log_list

    def emit(self, record):
        msg = self.format(record)
        LOG_QUEUE.append(msg)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(blue)s%(asctime)s: %(log_color)s%(levelname)-8s%(reset)s "
                      "%(white)s%(module)-11s %(lineno)-4s %(light_white)s%(message)s%(reset)s",
            "log_colors": {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
        },
        "file": {
            "format": "%(asctime)s %(levelname)-12s %(module)-12s %(lineno)-12s %(message)s",
        },
        "message_queue": {
            "format": "%(asctime)s %(levelname)s <span style='color: green;'>%(message)s</span>",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "file_debug": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "file",
            "filename": os.path.join("logs", "debug.log"),
        },
        "file_prod": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "file",
            "filename": os.path.join("logs", "production.log"),
        },
        "message_queue": {
            "level": "INFO",
            "()": ListHandler,
            "formatter": "message_queue",
            "log_list": LOG_QUEUE,
        },
    },
    "loggers": {
        "logger": {
            "handlers": ["console", "file_prod", "message_queue"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
        },
        "": {
            "handlers": ["file_debug"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
        },
    },
}

logs_path = BASEDIR / 'logs'
os.makedirs(logs_path, exist_ok=True)

logging.config.dictConfig(LOGGING_CONFIG)
