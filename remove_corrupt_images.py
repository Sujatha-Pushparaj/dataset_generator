import os
import magic


def remove(folder=''):
    # folder = '/home/soliton/work/projects/dataset_generator/data/neg_train_images/downloads/random'
    for filename in os.listdir(folder):
        infilename = os.path.join(folder, filename)
        m = magic.from_file(infilename, True).split('/')
        if(m[0] != 'image' or m[-1] not in ['jpg', 'jpeg', 'png']):
            os.remove(infilename)
            print("removed %s"%infilename)
            continue
#remove_corrupt()