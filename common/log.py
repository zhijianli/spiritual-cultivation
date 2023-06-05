import logging
import os
from .config import conf
from logging.handlers import TimedRotatingFileHandler


def _get_logger():
    level = conf().get('log_level')

    # home_dir = os.path.expanduser("~")
    log_dir = f"webchat_log"
    if not os.path.exists(log_dir) :
        os.mkdir(log_dir)
    
    log = logging.getLogger('log')

    if level == 'debug' :
        log.setLevel(logging.DEBUG)
    elif level == 'info' :
        log.setLevel(logging.INFO)
    else :
        log.setLevel(logging.ERROR)

    log_file = f"{log_dir}/log.txt"
    console_handle =  TimedRotatingFileHandler(filename=log_file, when='D', backupCount=7)
    console_handle.setFormatter(logging.Formatter('[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d] - %(message)s',
                                                  datefmt='%Y-%m-%d %H:%M:%S'))
    log.addHandler(console_handle)
    return log


# 日志句柄
logger = _get_logger()