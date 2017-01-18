import os
import time
import logging

# Script configuration
record_path = '/volume2/IPCam/FI9900P_00626E6B3E77/record/'
record_file_type = '.mkv'
maximum_age = 24*60*60 # seconds
log_level = logging.DEBUG

# Logging Configuration
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=log_level, filename='rotate.log')

# Start script
max_age_time = time.time() - maximum_age
files_deleted = 0

for filename in os.listdir(record_path):
    if os.path.getmtime(os.path.join(record_path,filename)) < max_age_time:
        if filename.endswith(record_file_type):
            # Recording is older than maximum allowed age
            logging.debug('Removing \'%s\' ...' % filename)
            os.remove(os.path.join(record_path,filename))
            files_deleted += 1;

logging.info('Recording rotation complete, deleted %d file(s).' % files_deleted)
