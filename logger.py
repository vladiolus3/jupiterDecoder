import os
import logging


def get_logger(name: str = None, level: int = logging.DEBUG, filename: str = "jupiterDecoder.log"):
    log_dir = os.path.normpath(os.getcwd())
    while log_dir.split(os.sep)[-1] != 'jupiterDecoder':
        log_dir = os.path.normpath(os.path.join(log_dir, os.pardir))
    log_dir = os.path.join(log_dir, 'logs')

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')
    file_handler = logging.FileHandler(os.path.join(log_dir, filename))
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
