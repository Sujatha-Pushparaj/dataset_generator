import os
import configparser
import image_aug.agum_rand
import datasetgenerator
import generate_images
import remove_corrupt_images
import queue
import timeit

def search(ret_queue, jobid = 'www23', searchtext='car', randomtext='random', tagscount=2, image_count_per_tag=25):
    driver = generate_images.open_browser()
    # searchtext = 'car'
    # randomtext = 'android'
    # tagscount = 5
    # tags_list is the list selected tag numbers
    all_class_tags = generate_images.get_all_tags(searchtext)[:int(tagscount)]
    tags_list = [i for i in range(int(tagscount))]
    start_tags_train = [0] * int(tagscount)
    image_count_train = [int(image_count_per_tag)] * int(tagscount)
    pos_image_links = generate_images.get_links(driver, searchtext, all_class_tags, tags_list, start_tags_train, image_count_train)
    generate_images.close_browser(driver)
    ret_queue.put({jobid: pos_image_links})


# search(queue.Queue(), 'www23', 'car', 'random', 2, 25)

'''
train_images():
    positive_train_image_path = './images' + '/' + jobid + '/training' + '/positive'
    if not (os.path.exists(positive_train_image_path)):
        os.makedirs(positive_train_image_path)
    negative_train_image_path = './images' + '/' + jobid + '/training' + '/negative'
    if not (os.path.exists(negative_train_image_path)):
        os.makedirs(negative_train_image_path)
    test_image_path = './images' + '/' + jobid + '/testing'
    if not (os.path.exists(test_image_path)):
        os.makedirs(test_image_path)
    tags_list = [i for i in range(int(tagscount))]
    start_tags_train = [0] * int(tagscount)
    image_count_train = [int(image_count_per_tag)] * int(tagscount)
    pos_image_links = generate_images.mul_tags(driver, searchtext, positive_train_image_path, all_class_tags, tags_list, start_tags_train, image_count_train)
    all_random_tags = generate_images.get_all_tags(randomtext)[:int(tagscount)]
    generate_images.mul_tags(driver, randomtext, negative_train_image_path, all_random_tags, tags_list, start_tags_train, image_count_train)
    generate_images.close_browser(driver)
    ret_queue.put({jobid: pos_image_links})


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
