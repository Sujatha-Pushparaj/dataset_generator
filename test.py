import glob
import os
import configparser
import image_aug.agum_rand
import datasetgenerator
import generate_images
import remove_corrupt_images

driver = generate_images.open_browser()
searchtext = 'car'
randomtext = 'android'
tagscount = 5
all_class_tags = generate_images.get_all_tags(searchtext)[:tagscount]
image_path =  "./images"
tags_list = [i for i in range(tagscount)]
start_tags_train = [0] * tagscount
image_count_train = [10] * tagscount
start_tags_predict = [11] * tagscount
image_count_predict = [20] * tagscount
generate_images.mul_tags(driver, searchtext, image_path + "/training/positive", all_class_tags, tags_list, start_tags_train, image_count_train)
all_random_tags = generate_images.get_all_tags(randomtext)[:tagscount]
generate_images.mul_tags(driver, randomtext, image_path + "/training/negative", all_random_tags, tags_list, start_tags_train, image_count_train)
generate_images.mul_tags(driver, searchtext, image_path + "/testing/positive", all_class_tags, tags_list, start_tags_predict , image_count_predict)
generate_images.close_browser(driver)


for agum_count in [5]:
    path = './images/training/positive'
    for tag in os.listdir(path):
        tag_path = os.path.join(path, tag)
        remove_corrupt_images.remove_corrupt(tag_path)
        image_aug.agum_rand.test_mul_image_agu(tag_path, agum_count)
    path = './images/training/negative'
    for tag in os.listdir(path):
        tag_path = os.path.join(path, tag)
        remove_corrupt_images.remove_corrupt(tag_path)
        image_aug.agum_rand.test_mul_image_agu(tag_path, agum_count)
    path = './images/testing/positive'
    for tag in os.listdir(path):
        tag_path = os.path.join(path, tag)
        remove_corrupt_images.remove_corrupt(tag_path)
    for nClusters in ['120']:
        config = configparser.ConfigParser()
        config.read('./models/dsgconfig.ini')
        config['Cluster']['number_of_clusters'] = nClusters
        with open('./models/dsgconfig.ini', 'w') as configfile:
            config.write(configfile)
        for contrast_threshold in [0.07]:
            d = datasetgenerator.DSG(contrast_threshold)
            d.train()
            d.predict()
            del(d)


    '''
    files = glob.glob('/home/soliton/work/projects/dataset_generator/images/training/positive/*.*')
    files.sort(key=os.path.getmtime)
    files.reverse()
    for i in range(training_size):
        os.remove(files[i])
    files2 = glob.glob('/home/soliton/work/projects/dataset_generator/images/training/negative/*.*')
    files2.sort(key=os.path.getmtime)
    files2.reverse()
    for i in range(training_size):
        os.remove(files2[i])
    '''
