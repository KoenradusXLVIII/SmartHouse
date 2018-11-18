import os
import time
import logging

# Script configuration
record_paths = ['/volume2/IPCam/FI9900P_00626E6B3E77/record/', '/volume2/IPCam/C1_00626E6DF234/record/']
record_file_type = '.mkv'
retention = 5 # days
maximum_age = retention*24*60*60 # seconds
log_level = logging.DEBUG

# Logging Configuration
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=log_level, filename='rotate.log')

# Start script
max_age_time = time.time() - maximum_age
files_deleted = 0

for record_path in record_paths:
	logging.debug('Processing path \'%s\'' % record_path)
	for filename in os.listdir(record_path):
		if os.path.getmtime(os.path.join(record_path,filename)) < max_age_time:
			if filename.endswith(record_file_type):
				# Recording is older than maximum allowed age
				logging.debug('Removing \'%s\' ...' % filename)
				os.remove(os.path.join(record_path,filename))
				files_deleted += 1;
			
logging.info('Recording rotation complete, deleted %d file(s).' % files_deleted)
