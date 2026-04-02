import logging


def configure_structured_logger(name: str, level: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
        )
    )
    logger.addHandler(handler)
    return logger
