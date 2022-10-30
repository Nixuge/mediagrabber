import logging


def set_logger_levels():
    logging.addLevelName(
        logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.DEBUG)) 
        # 37 = gray but blue good

    logging.addLevelName(
        logging.INFO, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.INFO))

    logging.addLevelName(
        logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))

    logging.addLevelName(
        logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))

    logger_format = "[%(levelname)s|%(filename)s:%(lineno)s@%(funcName)s] %(message)s"

    logging.basicConfig(format=logger_format, level=logging.DEBUG)
