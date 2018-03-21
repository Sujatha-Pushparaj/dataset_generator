import os
import magic
folder = '/home/soliton/work/projects/Images/downloads/car'
for filename in os.listdir(folder):
    infilename = os.path.join(folder, filename)
    m = magic.from_file(infilename, True).split('/')
    if(m[0] != 'image' or m[1] not in ['jpg', 'jpeg', 'html', 'htm', 'php']):
        os.remove(infilename)
        print("removed %s"%infilename)
        continue
    filename_ext = filename.split('.')
    if(filename_ext[1] not in ['jpg', 'jpeg']):
        os.rename(infilename, os.path.join(folder, filename_ext[0] + '.jpeg'))
        print("renamed %s"%infilename)
