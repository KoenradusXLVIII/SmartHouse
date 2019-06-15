import os
from PIL import Image

input_path = 'S:\\WCAU45115692\\Negatives'
output_path = 'S:\\WCAU45115692\\Negatives\low_res'

for root, dirs, files in os.walk(input_path, topdown=False):
    for name in files:
        print(os.path.join(root, name))
        if os.path.splitext(os.path.join(root, name))[1].lower() == ".tif":
            if os.path.isfile(os.path.splitext(os.path.join(output_path, name))[0] + ".jpg"):
                print("A jpeg file already exists for %s" % name)
            # If a jpeg with the name does *NOT* exist, covert one from the tif.
            else:
                outputfile = os.path.splitext(os.path.join(output_path, name))[0] + ".jpg"
                try:
                    im = Image.open(os.path.join(root, name))
                    print("Converting jpeg for %s" % name)
                    size = tuple(ti / 4 for ti in im.size)
                    im.thumbnail(size)
                    im.save(outputfile, "JPEG", quality=100)
                except Exception as e:
                    print(e)