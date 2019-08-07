import os
from PIL import Image
import time

input_path = 'S:\\WCAU45115692\\Negatives'
output_path = 'S:\\WCAU45115692\\Negatives\low_res'
input_files = 0
output_files = 0

start = time.time()

for root, dirs, files in os.walk(input_path, topdown=False):
    for name in files:
        if os.path.splitext(os.path.join(root, name))[1].lower() == ".tif":
            input_files += 1
            if not os.path.isfile(os.path.splitext(os.path.join(output_path, name))[0] + ".jpg"):
                # If a jpeg with the name does *NOT* exist, covert one from the tif.
                outputfile = os.path.splitext(os.path.join(output_path, name))[0] + ".jpg"
                output_files += 1
                try:
                    im = Image.open(os.path.join(root, name))
                    print("Converting jpeg for %s" % name)
                    size = tuple(ti / 4 for ti in im.size)
                    im.thumbnail(size)
                    im.save(outputfile, "JPEG", quality=100)
                except Exception as e:
                    print(e)

stop = time.time()

print('Converted %d files out of a total of %d files in %d seconds' % (output_files, input_files, stop-start))