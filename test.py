import glob
import os
import configparser
import image_aug.agum_rand
import datasetgenerator
for training_size in [20, 60]:
    image_aug.agum_rand.test_mul_image_agu('/home/soliton/work/projects/dataset_generator/images2/training/positive', training_size)
    image_aug.agum_rand.test_mul_image_agu('/home/soliton/work/projects/dataset_generator/images2/training/negative', training_size)
    for nClusters in ['100','120']:
        config = configparser.ConfigParser()
        config.read('/home/soliton/work/projects/dataset_generator/models/dsgconfig.ini')
        config['Cluster']['number_of_clusters'] = nClusters
        with open('/home/soliton/work/projects/dataset_generator/models/dsgconfig.ini', 'w') as configfile:
            config.write(configfile)
        for contrast_threshold in [0.06, 0.07]:
            d = datasetgenerator.DSG(contrast_threshold)
            d.train()
            d.predict(True)
            del(d)
    files = glob.glob('/home/soliton/work/projects/dataset_generator/images2/training/positive/*.*')
    files.sort(key=os.path.getmtime)
    files.reverse()
    for i in range(training_size):
        os.remove(files[i])
    files2 = glob.glob('/home/soliton/work/projects/dataset_generator/images2/training/negative/*.*')
    files2.sort(key=os.path.getmtime)
    files2.reverse()
    for i in range(training_size):
        os.remove(files2[i])
