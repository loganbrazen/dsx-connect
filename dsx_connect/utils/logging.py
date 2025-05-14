import os

import sys
import logging
import colorlog


dsx_logging = logging.getLogger("dpa-proxy")
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
dsx_logging.setLevel(level=log_level)
dsx_logging.propagate = False  # Prevent the logger from propagating messages to the root logger


# Define colors for each log level
log_colors = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'bold_red',
    'CRITICAL': 'bold_red,bg_white',
}

log_format = '%(log_color)s%(asctime)s %(levelname)-8s %(filename)-20s: %(message)s'
error_format = '%(log_color)s%(asctime)s %(levelname)-8s %(filename)-20s:%(lineno)d: %(message)s'

# Create a color formatter
# formatter = colorlog.ColoredFormatter(log_format, log_colors=log_colors)

# Create the formatters using ColoredFormatter
default_formatter = colorlog.ColoredFormatter(log_format, log_colors=log_colors)
error_formatter = colorlog.ColoredFormatter(error_format, log_colors=log_colors)


# Create a custom handler to switch formatters based on log level
class CustomLogHandler(logging.StreamHandler):
    def emit(self, record):
        # Use the error formatter for error and higher levels, otherwise use the default formatter
        if record.levelno >= logging.ERROR:
            self.setFormatter(error_formatter)
        else:
            self.setFormatter(default_formatter)
        super().emit(record)

# Add the custom handler to the logger
if not dsx_logging.handlers:
    custom_handler = CustomLogHandler()
    dsx_logging.addHandler(custom_handler)
# Create a console handler with the specified format
# Create and add the console handler if it doesn't already exist
if not dsx_logging.handlers:
    custom_handler = CustomLogHandler()
    dsx_logging.addHandler(custom_handler)
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # dpx_logging.addHandler(console_handler)

dsx_logging.info(f'Log level set to {log_level}')

# class CustomStdoutHandler(logging.StreamHandler):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.default_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#         self.error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')
#
#     # self.default_formatter = logging.Formatter('%(asctime)s:| %(message)s')
#     #     self.error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [line:%(lineno)d] - %(message)s')
#
#     def emit(self, record):
#         # Apply the appropriate formatter based on the log level
#         if record.levelno >= logging.ERROR:
#             self.setFormatter(self.error_formatter)
#         else:
#             self.setFormatter(self.default_formatter)
#
#         # Call the parent class's emit() method
#         super().emit(record)
#
#
# class CustomFileHandler(logging.FileHandler):
#     def __init__(self, filename, *args, **kwargs):
#         super().__init__(filename, *args, **kwargs)
#         self.default_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#         self.error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s')
#
#     def emit(self, record):
#         # Apply the appropriate formatter based on the log level
#         if record.levelno >= logging.ERROR:
#             self.setFormatter(self.error_formatter)
#         else:
#             self.setFormatter(self.default_formatter)
#
#         # Call the parent class's emit() method
#         super().emit(record)
#
#
# main_logger_name = 'main'
#
# def create_stdout_logger(logger_name, log_level = logging.DEBUG, propagate: bool = False):
#     logger = logging.getLogger(main_logger_name)
#     logger.propagate = propagate
#     logger.setLevel(log_level)
#
#     # Check if the logger already has a handler for the file
#     if not any(isinstance(hdlr, logging.StreamHandler) for hdlr in logger.handlers):
#         handler = CustomStdoutHandler()
#         logger.addHandler(handler)
#
#     return logger
#
# def create_file_logger(logger_name='main', filename='main', propagate: bool = True):
#     # Use a fixed logger name to ensure all calls refer to the same logger
#     global main_logger_name
#     main_logger_name = logger_name
#
#     logger = logging.getLogger(main_logger_name)
#     logger.propagate = propagate
#     logger.setLevel(logging.DEBUG)
#
#     # Check if the logger already has a handler for the file
#     if not any(isinstance(hdlr, logging.FileHandler) for hdlr in logger.handlers):
#         handler = CustomFileHandler(filename)
#         logger.addHandler(handler)
#
#     return logger
#
# def get_logger(logger_name):
#     # Retrieve the main file logger
#     main_logger = logging.getLogger(main_logger_name)
#
#     # Create a new logger with the name of the calling module
#     logger = logging.getLogger(logger_name)
#     # logger.propagate = False  # Ensure messages propagate to the main logger
#     log_level = main_logger.getEffectiveLevel()
#     logger.setLevel(log_level)
#
#     # Add a handler to the new logger that references the main logger's handlers
#     for handler in main_logger.handlers:
#         logger.addHandler(handler)
#
#     return logger