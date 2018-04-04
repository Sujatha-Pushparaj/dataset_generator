import os
import configparser
import image_aug.agum_rand
import datasetgenerator
import generate_images
import remove_corrupt_images
import queue
# import timeit
import ipdb
ipdb.set_trace()


def search(ret_queue, jobid = 'www23', searchtext='car', randomtext='random', tagscount=2, image_count_per_tag=25, config_path='./data'):
    driver = generate_images.open_browser()
    # list of tags
    all_class_tags = generate_images.get_all_tags(searchtext)[:int(tagscount)]
    tags_list = [i for i in range(int(tagscount))]
    # list of tag start numbers , id of last downloaded image
    start_tags_train, last_img_id = get_tag_start(config_path, all_class_tags,
                                                  int(image_count_per_tag))
    # list of image counts for each tag
    image_count_train = [int(image_count_per_tag)] * int(tagscount)
    # get image details(list of dictionary (id,url,type,tag))
    images_det, last_img_id = generate_images.get_links(
        driver, searchtext, all_class_tags, tags_list, start_tags_train,
        image_count_train, int(last_img_id))
    # return the images details via queue
    ret_queue.put({jobid: (images_det, all_class_tags)})
    generate_images.close_browser(driver)
    # update last image id in configuration file
    config = configparser.ConfigParser()
    config.read(config_path)
    config['Details']['last_img_id'] = last_img_id
    with open(config_path, 'w') as configfile:
        config.write(configfile)


def download_training_images(user_id, searchtext, images_det):
    driver = generate_images.open_browser()
    search_path = os.path.join('./data', user_id, searchtext)
    positive_train_image_path = os.path.join(search_path, 'pos_train_images')
    if not (os.path.exists(positive_train_image_path)):
        os.makedirs(positive_train_image_path)
    generate_images.download_img(driver, positive_train_image_path,
                                 images_det)
    generate_images.close_browser(driver)
    remove_corrupt_images.remove(positive_train_image_path)


def get_tag_start(config_path, all_class_tags, image_count_per_tag):
    config = configparser.ConfigParser()
    config.read(config_path)
    tag_start = []
    existing_tags = config.options('Details')
    for tag in all_class_tags:
        if tag is None or tag == 'None':
            tag_valid = 'none'
        else:
            tag_valid = tag.replace(':', '', 1)
        print(tag_valid, type(tag_valid), existing_tags)
        if(tag_valid in existing_tags):
            tag_start.append(int(config['Details'][tag_valid]))
            config['Details'][tag_valid] = str(image_count_per_tag + int(config['Details'][tag_valid]))
            continue
        config['Details'][tag_valid] = str(image_count_per_tag)
        tag_start.append(0)
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    print("#########################", tag_start)
    return tag_start, config['Details']['last_img_id']


def train(ret_queue, user_id, searchtext, images_det, dl_thread):
    search_path = os.path.join('./data', user_id, searchtext)
    positive_train_image_path = os.path.join(search_path, 'pos_train_images')
    negative_train_image_path = os.path.join('./data', 'neg_train_images')
    train_obj = datasetgenerator.DSG()
    train_obj.model_path = os.path.join(search_path, 'model.file')
    train_obj.positive_training_images_path = positive_train_image_path
    train_obj.random_training_images_path = negative_train_image_path
    # wait for download to complete
    dl_thread.join()
    remove_rejected(positive_train_image_path, images_det)
    train_obj.train()


def remove_rejected(path, images_det):
    sel_images = []
    for image in images_det:
        sel_images.append(image['ID'] + '.' + image['type'])
    for image in os.listdir(path):
        if image not in sel_images:
            os.remove(os.path.join(path, image))


def download_for_prediction(ret_queue, user_id, searchtext, sel_tags, imagecount, config_path):
    driver = generate_images.open_browser()
    image_count_per_tag = int(imagecount / len(sel_tags))
    start_tags, last_img_id_str = get_tag_start(
        config_path, sel_tags, image_count_per_tag)
    predict_image_path = os.path.join('./data', user_id, searchtext,
                                      'predict_images')
    last_img_id = int(last_img_id_str)
    # create folder if not exists
    if not (os.path.exists(predict_image_path)):
        os.makedirs(predict_image_path)
    # download the images for prediction
    '''
    last_img_id = generate_images.download_images_for_prediction(
        driver, searchtext, predict_image_path, sel_tags, tags_list,
        start_tags, image_count_predict, int(last_img_id))
    '''
    extensions = ["jpg", "jpeg", "png"]
    for i, tag in enumerate(sel_tags):
        if tag is None:
            tag = "None"
        images_det = []
        tag_path = os.path.join(predict_image_path, tag)
        image_links_types = generate_images.fetch_links(
            driver, searchtext=searchtext, start=start_tags[i],
            count_argv=image_count_per_tag, tags=tag,
            extensions=extensions)
        for a_image in image_links_types:
            last_img_id += 1
            image_det = {"ID": str(last_img_id), "tag": tag,
                         "url": a_image[0], "type": a_image[1]}
            images_det.append(image_det)
        generate_images.download_img(driver, tag_path, images_det)
        remove_corrupt_images.remove(tag_path)

    # update configuration file
    config = configparser.ConfigParser(strict=False)
    config.read(config_path)
    config['Details']['last_img_id'] = str(last_img_id)
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    generate_images.close_browser(driver)

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
