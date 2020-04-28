# Public imports
import os
import filecmp
from shutil import copyfile
import logging
from datetime import datetime
import time

# Private imports

# Configuration variables
backup_src = '/home/pi/WCAU45115692'
backup_dirs = ['Negatives', 'Photos', 'Spark', 'GoPro', 'Documents']
backup_dst = '/home/pi/WCAU45635050/Backup'

# Functions
def talk_log(msg, level='info'):
    print('%s' % msg)
    if level == 'info':
        logging.info('%s' % msg)
    elif level == 'warning':
        logging.warning('%s' % msg)
    logger = logging.getLogger()
    logger.handlers[0].flush()

# Main Program
if __name__ == '__main__':
    # Initialize logging
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = os.path.dirname(os.path.realpath(__file__))
    logfileName = '%s.log' % now
    logging.basicConfig(filename=os.path.join(script_path, logfileName), filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    talk_log('= JSync configuration =')
    talk_log('Process running with PID: %d' % os.getpid())
    talk_log('Log file location: %s' % os.path.join(script_path, logfileName))
    talk_log('Backup source: %s' % backup_src)
    talk_log('Backup directories: %s' % ', '.join(backup_dirs))
    talk_log('Backup destination: %s' % backup_dst)
    talk_log('')

    # Walk through backup source directory and backup any files that need it
    new = 0
    updated = 0
    start = time.time()
    for backup_dir in backup_dirs:
        for root, subdirs, files in os.walk(os.path.join(backup_src, backup_dir)):
            talk_log('Processing folder: %s [%d files]' % (root, len(files)))

            # Extract directory to backup to
            backup_dir = os.path.join(backup_dst)
            for dir in root.split(os.sep)[4:]:
                backup_dir = os.path.join(backup_dir, dir)

            # Create directory if it does not exist
            if not os.path.exists(backup_dir):
                talk_log('Creating new directory: %s' % backup_dir)
                os.makedirs(backup_dir)

            files.sort()
            for file in files:
                file_src = os.path.join(root, file)
                file_dst = os.path.join(backup_dir, file)

                if not os.path.exists(file_dst):
                    # Check if file exists, if not copy
                    talk_log('Found new file to backup: %s' % file)
                    new += 1
                    copyfile(file_src, file_dst)
                elif not filecmp.cmp(file_src, file_dst):
                    # If file exists, check if it is updated
                    # If it is overwrite the backup with the updated file
                    talk_log('Found updated file to backup: %s' % file)
                    updated += 1
                    copyfile(file_src, file_dst)

    elapsed_time = time.time() - start
    talk_log('JSync completed in %d minutes. %d new files copied. %d files updated.' % (elapsed_time / 60, new, updated))
