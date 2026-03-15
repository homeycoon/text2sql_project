import logging


def get_logger(logger_name: str) -> logging.Logger:
    """
    Функция, возвращающая логгер со стандартными настройками

    :param logger_name: имя логгера
    :return: объект логгер
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        fmt='%(filename)s:%(lineno)d #%(levelname)-10s '
            '[%(asctime)s] - %(name)s - %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(fmt=fmt)

    logger.addHandler(handler)

    return logger
