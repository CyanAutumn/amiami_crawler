import os
import logging
from datetime import datetime

FOLDER = r"./log/"
PATH = rf'{FOLDER}{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.log'


class Flogger(object):
    def __init__(self) -> None:
        # 初始化方法log = tlogger.Flogger().get_logger(__name__)
        log_format = "%(asctime)s [%(filename)s]  [%(levelname)s] - %(message)s"

        if not os.path.exists(FOLDER):
            os.makedirs(FOLDER)

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        # 调用模块时,如果错误引用，比如多次调用，每次会添加Handler，造成重复日志，这边每次都移除掉所有的handler，后面在重新添加，可以解决这类问题
        while self.logger.hasHandlers():
            for i in self.logger.handlers:
                self.logger.removeHandler(i)

        # 创建文件处理程序
        file_handler = logging.FileHandler(PATH, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))

        # 创建控制台处理程序
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))

        # 将处理程序添加到日志对象
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self, name):
        return logging.getLogger(name)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def exception(self, message):
        self.logger.exception(message)
