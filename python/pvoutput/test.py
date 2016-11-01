import os
import time
import sys

st = os.stat('test.py')
age = (time.time()-st.st_mtime)
print age
print sys.argv[1]
