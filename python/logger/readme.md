# Logger module
## Introduction
The Logger module can be used to access the logging capability both on Windows and Linux platforms.
It automatically detects the platform and sets the logging handlers accordingly.

## Usage example
```Python
from logger import Logger

# Set up simple logger with default log level, which is informational
log_client = Logger('My logger')
# Set up a logger with warning as default log level
log_client = Logger('My warning logger', 'warning')

# Post a message to the logger
log_client.debug('This is a debug message')
log_client.info('This is an information message')
log_client.warning('This is a warning message')
log_client.error('This is an error message')
log_client.critical('This is a critical message')