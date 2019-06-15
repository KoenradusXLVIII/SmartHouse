import platform
import os
import time

# Directory configuration
if platform.system() == 'Windows':
    dirs = ['S:\\WCAU45635050\\webcam\\C1_00626E6DF234\\record', 'S:\\WCAU45635050\\webcam\\FI9900P_00626E6B3E77\\record']
elif platform.system() == 'Linux':
    dirs = ['/home/pi/WCAU45635050/webcam/C1_00626E6DF234/record', '/home/pi/WCAU45635050/webcam/FI9900P_00626E6B3E77/record']

# Script configuration
keep_days = 7

now = time.time()
for dir in dirs:
    for fp in os.listdir(dir):
        fp = os.path.join(dir, fp)
        if '.mkv' in fp:
            print('Processing file %s' % fp)
            if os.stat(fp).st_mtime < now - (keep_days * 86400):
                if os.path.isfile(fp):
                    print('Removing file %s' % fp)
                    os.remove(fp)