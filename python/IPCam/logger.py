import platform
import logging.handlers


class Logger:
    def __init__(self, name, log_level='info'):
        # Store local variables
        self.name = name
        self.log_level = log_level.lower()

        # Create logging instance
        self.logger = logging.getLogger(self.name)
        self.formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')

        # Initialise and add logging handler (platform dependent)
        if platform.system() == 'Windows':
            self.handler = logging.StreamHandler()
        elif platform.system() == 'Linux':
            self.handler = logging.handlers.SysLogHandler(address='/dev/log')
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

        # Set log level
        self.set_log_level(log_level)

    def set_log_level(self, log_level):
        # Set new log level
        self.log_level = log_level.lower()
        if self.log_level == 'debug':
            new_log_level = logging.DEBUG
        elif self.log_level == 'info':
            new_log_level = logging.INFO
        elif self.log_level == 'warning':
            new_log_level = logging.WARNING
        elif self.log_level == 'error':
            new_log_level = logging.ERROR
        elif self.log_level == 'critical':
            new_log_level = logging.CRITICAL

        self.logger.setLevel(new_log_level)
        self.handler.setLevel(new_log_level)

    def get_log_level(self):
        # Return current log level
        return self.log_level

    def debug(self, message):
        # Log informational message
        self.logger.debug(message)

    def info(self, message):
        # Log informational message
        self.logger.info(message)

    def warning(self, message):
        # Log informational message
        self.logger.warning(message)

    def error(self, message):
        # Log informational message
        self.logger.error(message)

    def error(self, message):
        # Log informational message
        self.logger.critical(message)
