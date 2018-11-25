import platform
import logging.handlers


class Client:
    # noinspection SpellCheckingInspection
    def __init__(self, name, log_level='info'):
        # Store local variables
        self.name = name
        self.log_level = log_level.lower()

        # Create logging instance
        self.formatter = logging.Formatter('%(name)s [%(levelname)s] %(message)s')
        self.logger = logging.getLogger(self.name)
        self.set_log_level(log_level)

        # Initialise and add logging handler (Linux only)
        if platform.system() == 'Linux':
            self.handler = logging.handlers.SysLogHandler(address='/dev/log')
            self.handler.setLevel(self.log_level)
            self.handler.setFormatter(self.formatter)
            self.logger.addHandler(self.handler)

    def set_log_level(self, log_level):
        # Set new log level
        self.log_level = log_level.lower()
        if self.log_level == 'debug':
            self.logger.setLevel(logging.DEBUG)
        elif self.log_level == 'info':
            self.logger.setLevel(logging.INFO)
        elif self.log_level == 'warning':
            self.logger.setLevel(logging.WARNING)
        elif self.log_level == 'error':
            self.logger.setLevel(logging.ERROR)

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
