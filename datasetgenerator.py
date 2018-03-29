
# coding: utf-8
import configparser
import csv
import os
import pickle
import timeit

import cv2
from cv2.xfeatures2d import SIFT_create
import numpy as np
from sklearn import cluster
from sklearn.svm import SVC
from sklearn.metrics import precision_score, recall_score

config_path = './models/dsgconfig.ini'
class_labels = {'positive': 1, 'negative': 0}


class DSG(object):

    def __init__(self, contrast_threshold=0.1):
        self.__configure()
        self.contrast_threshold = contrast_threshold
        self.sift = SIFT_create(contrastThreshold=self.contrast_threshold)
        self.orb = cv2.ORB()
        # nfeatures,contrastThreshold,edgethreshold,nOctaveLayers=3,sigma=1.5
        self.hog = cv2.HOGDescriptor()
        self.classifier = SVC(C=1, kernel='rbf', probability=True)
        # C inversely proportional to regularisation
        self.features_len = []
        self.all_features = np.array([[]])
        self.trainimage_label = []
        self.test_set = np.array([[]])
        self.testimage_list = []
        self.testimage_label = []
        self.trainingtime = 0
        self.predictiontime = 0

    def __configure(self):
        global config_path
        config = configparser.ConfigParser()
        config.read(config_path)
        self.positive_training_images_path = config['Paths']['positive_training_images_path']
        self.random_training_images_path = config['Paths']['random_training_images_path']
        self.positive_testing_images_path = config['Paths']['positive_testing_images_path']
        self.random_testing_images_path = config['Paths']['random_testing_images_path']
        self.resize_height = int(config['Image']['resize_height'])
        self.resize_width = int(config['Image']['resize_width'])
        self.number_of_clusters = int(config['Cluster']['number_of_clusters'])
        self.model_path = config['Paths']['model_path']

    def __build_train_featureset(self, path, trainimage_label):
        print("loading trainingset", path)
        for tag in os.listdir(path):
            tag_path = os.path.join(path, tag)
            for image in os.listdir(tag_path):
                complete_path = os.path.join(tag_path, image)
                des = self.__get_features_sift(complete_path)
                print ('Complete Path========>', complete_path)
                if des is None:
                    continue
                self.features_len.append(len(des))
                self.trainimage_label.append(trainimage_label)
                if(self.all_features.shape == (1, 0)):
                    self.all_features = np.array(des)
                else:
                    self.all_features = np.concatenate((self.all_features,
                                                        des), axis=0)

    def __cleartraining(self):
        self.all_features = np.array([[]])
        self.features_len = []
        self.trainimage_label = []

    def __get_features_sift(self, path):
        try:
            img = cv2.imread(path, 1)
            re_img = cv2.resize(img, (self.resize_height, self.resize_width))
            gray = cv2.cvtColor(re_img, cv2.COLOR_BGR2GRAY)
            kp, des = self.sift.detectAndCompute(gray, None)
            return des
        except Exception:
            return None

    def __get_features_orb(self, path):
        img = cv2.imread(path, 1)
        re_img = cv2.resize(img, (self.resize_height, self.resize_width))
        gray = cv2.cvtColor(re_img, cv2.COLOR_BGR2GRAY)
        kp = self.orb.detect(gray, None)
        kp, des = self.orb.compute(gray, kp)
        return des

    def __get_features_hog(self, path):
        img = cv2.imread(path, 1)
        re_img = cv2.resize(img, (self.resize_height, self.resize_width))
        gray = cv2.cvtColor(re_img, cv2.COLOR_BGR2GRAY)
        des = self.hog.compute(gray)
        return des

    def __cluster(self):
        print(len(self.all_features))
        self.__k_means()
        print(len(self.centroids))

    def __k_means(self):
        self.centroids, self.cluster_labels, _ = cluster.k_means(
            self.all_features, self.number_of_clusters, random_state=77)

    def __meanshift(self):
        self.centroids, self.cluster_labels = cluster.mean_shift(
            self.all_features)

    def train(self):
        global class_labels
        self.trainingtime = timeit.default_timer()
        self.__cleartraining()
        self.__build_train_featureset(self.positive_training_images_path,
                                      class_labels['positive'])
        self.__build_train_featureset(self.random_training_images_path,
                                      class_labels['negative'])
        self.__cluster()
        training_data = np.zeros((len(self.trainimage_label),
                                  max(self.cluster_labels) + 1))
        feature_index = 0
        for image in range(len(self.trainimage_label)):
            for feature in range(self.features_len[image]):
                training_data[image][self.cluster_labels[feature_index]] += 1
                feature_index += 1
        self.classifier.fit(training_data, self.trainimage_label)
        self.trainingtime = timeit.default_timer() - self.trainingtime
        self.__store_model()

    def __cleartesting(self):
        self.test_set = np.array([[]])
        self.testimage_label = []
        self.testimage_list = []

    def __build_test_featureset(self, path, flag=-1):
        print("loading testset")
        for tag in os.listdir(path):
            tag_path = os.path.join(path, tag)
            for image in os.listdir(tag_path):
                complete_path = os.path.join(tag_path, image)
                des = self.__get_features_sift(complete_path)
                if des is None:
                    continue
                self.testimage_list.append(complete_path)
                self.testimage_label.append(flag)
                test_set = np.zeros((1, max(self.cluster_labels) + 1))
                for feature in des:
                    dis = abs(self.centroids - feature)
                    dis_sum = [sum(i) for i in dis]
                    bst_label = dis_sum.index(min(dis_sum))
                    test_set[0][bst_label] += 1
                if(self.test_set.shape == (1, 0)):
                    self.test_set = np.array(test_set)
                else:
                    self.test_set = np.concatenate((self.test_set, test_set),
                                                   axis=0)

    def predict(self, report=False):
        global class_labels
        self.__load_model()
        self.predictiontime = timeit.default_timer()
        self.__cleartesting()
        self.__build_test_featureset(self.positive_testing_images_path,
                                     class_labels['positive'])
        #self.__build_test_featureset(self.random_testing_images_path,
        #                             class_labels['negative'])
        result = self.__format_result(self.classifier.
                                      predict_proba(self.test_set)[:, 1])
        self.predictiontime = timeit.default_timer() - self.predictiontime
        if report:
            self.__generate_report(result)
        self.__show_images(result)
        return result

    def __format_result(self, class_prob):
        self.testimage_list = [x for _, x in sorted(zip(class_prob,
                                                    self.testimage_list))]
        self.testimage_label = [x for _, x in sorted(zip(class_prob,
                                                     self.testimage_label))]
        class_prob.sort()
        class_prob = class_prob[::-1]
        self.testimage_list.reverse()
        self.testimage_label.reverse()
        result = [[value0, value1, value2] for value0, value1, value2
                  in zip(self.testimage_list, self.testimage_label,
                         class_prob)]
        print(self.classifier.classes_)
        return result

    def __show_images(self, result):
        for image in result:
            print(image)
            temp = cv2.imread(image[0], 1)
            temp = cv2.resize(temp, (100, 100))
            cv2.imshow(str(image[2]), temp)
            cv2.waitKey()
            cv2.destroyAllWindows()

    def __store_model(self):
        model = {}
        model['classfier'] = self.classifier
        model['centroids'] = self.centroids
        model['cluster_labels'] = self.cluster_labels
        file_name = 'carmodel_' + str(self.number_of_clusters) + '_' + str(self.contrast_threshold) + '.file'
        with open(self.model_path + '/' + file_name, 'wb') as f:
            pickle.dump(model, f)

    def __load_model(self):
        file_name = 'carmodel_' + str(self.number_of_clusters) + '_' + str(self.contrast_threshold) + '.file'
        with open(self.model_path + '/' + file_name, 'rb') as f:
            model = pickle.load(f)
        #self.sift = cv2.xfeatures2d.SIFT_create(contrastThreshold=0.1)
        self.classifier = model['classfier']
        self.centroids = model['centroids']
        self.cluster_labels = model['cluster_labels']

    def __score(self, predicted_label, threshold, result):
        hp, lp, hn, ln, x = 0, 0, 0, 0, 0
        for a, b, rst in zip(predicted_label, self.testimage_label, result):
            if(rst[2] >= threshold or rst[2] <= (1 - threshold)):
                if(a == b):
                    hp += 1
                    x += 1
                else:
                    hn += 1
            else:
                if(a == b):
                    lp += 1
                    x += 1
                else:
                    ln += 1
        return x / len(self.testimage_label), hp, lp, hn, ln

    def __generate_report(self, result):
        with open('report.csv', 'a', newline='') as csvfile:
            wr = csv.writer(csvfile, delimiter=',')
            if(os.stat("report.csv").st_size == 0):
                wr.writerow(['PositiveTraining', 'NegativeTraining',
                            'Clustercount', 'contrastThreshold', 'Threshold',
                             'Accuracy', 'HP', 'LP', 'HN', 'LN',
                             'TrainingTime', 'PredictionTime',
                             'Precision', 'Recall'])
            x = []
            for i in result:
                x.append(i[2] > 0.5)
            x = list(map(int, x))
            for threshold in [0.6, 0.7, 0.8]:
                random_training = sum(self.trainimage_label)
                positive_training = len(self.trainimage_label) - random_training
                row = [positive_training, random_training]
                row.extend([len(self.centroids), self.contrast_threshold, threshold])
                row.extend(self.__score(x, threshold, result))
                row.append(self.trainingtime)
                row.append(self.predictiontime)
                row.append(precision_score(self.testimage_label, x))
                row.append(recall_score(self.testimage_label, x))
                wr.writerow(row)


if __name__ == '__main__':
    dsg = DSG()
    dsg.train()
    result = dsg.predict()
