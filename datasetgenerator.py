
# coding: utf-8

import cv2
from cv2.xfeatures2d import SIFT_create
import os
import csv
import configparser
import numpy as np
from sklearn import cluster
import pickle
from sklearn.svm import SVC
import timeit


class DSG:

    def __init__(self, contrast_threshold=0.1):
        self.config_path = './models/dsgconfig.ini'
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
        config = configparser.ConfigParser()
        config.read(self.config_path)
        self.positive_training_images = config['Paths']['positive_training_images']
        self.random_training_images = config['Paths']['random_training_images']
        self.positive_testing_images = config['Paths']['positive_testing_images']
        self.random_testing_images = config['Paths']['random_testing_images']
        self.resize_height = int(config['Image']['resize_height'])
        self.resize_width = int(config['Image']['resize_width'])
        self.number_of_clusters = int(config['Cluster']['number_of_clusters'])
        self.model_path = config['Paths']['model_path']

    def __load_trainingset(self, path, trainimage_label):
        print("loading trainingset", path)
        for image in os.listdir(path):
            self.__trainingset(path + '/' + image, trainimage_label)

    def __trainingset(self, image_path, trainimage_label):
        des = self.__get_features_sift(image_path)
        if des is None:
            return None
        self.features_len.append(len(des))
        self.trainimage_label.append(trainimage_label)
        if(self.all_features.shape == (1, 0)):
            self.all_features = np.array(des)
        else:
            self.all_features = np.concatenate((self.all_features, des),
                                               axis=0)

    def __cleartraining(self):
        self.all_features = np.array([[]])
        self.features_len = []
        self.trainimage_label = []

    def __get_features_sift(self, path):
        img = cv2.imread(path, 1)
        re_img = cv2.resize(img, (self.resize_height, self.resize_width))
        gray = cv2.cvtColor(re_img, cv2.COLOR_BGR2GRAY)
        kp, des = self.sift.detectAndCompute(gray, None)
        return des

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
        self.__k_means()
        print(len(self.centroids), len(self.all_features))

    def __k_means(self):
        self.centroids, self.cluster_labels, _ = cluster.k_means(
            self.all_features, self.number_of_clusters, random_state=77)

    def __meanshift(self):
        self.centroids, self.cluster_labels = cluster.mean_shift(
            self.all_features, bandwidth=360)

    def train(self):
        self.trainingtime = timeit.default_timer()
        self.__cleartraining()
        self.__load_trainingset(self.positive_training_images, 0)
        self.__load_trainingset(self.random_training_images, 1)
        self.__cluster()
        training_data = np.zeros((len(self.trainimage_label),
                                  max(self.cluster_labels) + 1))
        feature_index = 0
        for image in range(len(self.trainimage_label)):
            for feature in range(self.features_len[image]):
                training_data[image][self.cluster_labels[feature_index]] = 1
                + training_data[image][self.cluster_labels[feature_index]]
                feature_index += 1
        self.classifier.fit(training_data, self.trainimage_label)
        self.trainingtime = timeit.default_timer() - self.trainingtime

    def __cleartesting(self):
        self.test_set = np.array([[]])
        self.testimage_label = []
        self.testimage_list = []

    def __load_testset(self, path, flag=-1):
        print("loading testset")
        for image in os.listdir(path):
            self.testimage_list.append(image)
            self.testimage_label.append(flag)
            self.__testset(path + '/' + image)

    def __testset(self, imagepath):
        test_set = np.zeros((1, max(self.cluster_labels) + 1))
        des = self.__get_features_sift(imagepath)
        for feature in des:
            low_dif, bst_label = 0, 0
            for label in range(len(self.centroids)):
                dist = sum(abs(self.centroids[label] - feature))
                if(low_dif == 0 or dist <= low_dif):
                    low_dif = dist
                    bst_label = label
            test_set[0][bst_label] += 1
        if(self.test_set.shape == (1, 0)):
            self.test_set = np.array(test_set)
        else:
            self.test_set = np.concatenate((self.test_set, test_set), axis=0)

    def predict(self, report=False):
        self.predictiontime = timeit.default_timer()
        self.__cleartesting()
        self.__load_testset(self.positive_testing_images, 0)
        self.__load_testset(self.random_testing_images, 1)
        result = self.__format_result(self.classifier.
                                      predict_proba(self.test_set)[:, 0])
        self.predictiontime = timeit.default_timer() - self.predictiontime
        if report:
            self.__generate_report(result)
        return result

    def __format_result(self, result):
        self.testimage_list = [x for _, x in sorted(zip(result,
                                                    self.testimage_list))]
        self.testimage_label = [x for _,
                                x in sorted(zip(result, self.testimage_label))]
        result.sort()
        result = result[::-1]
        self.testimage_list.reverse()
        self.testimage_label.reverse()
        result = [[value0, value1, value2] for value0, value1, value2
                  in zip(self.testimage_list, self.testimage_label, result)]
        print(self.classifier.classes_)
        return result

    def store_model(self):
        model = {}
        model['classfier'] = self.classifier
        model['centroids'] = self.centroids
        model['cluster_labels'] = self.cluster_labels
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)

    def load_model(self):
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        self.sift = cv2.xfeatures2d.SIFT_create(contrastThreshold=0.1)
        self.classifier = model['classfier']
        self.centroids = model['centroids']
        self.cluster_labels = model['cluster_labels']

    def __score(self, predicted_label):
        hp, lp, hn, ln, x = 0, 0, 0, 0, 0
        for a, b in zip(predicted_label, self.testimage_label):
            if(a > b):
                lp = lp + 1
            elif(b > a):
                hn = hn + 1
            elif(a == 1):
                ln = ln + 1
                x = x + 1
            else:
                hp = hp + 1
                x = x + 1
        return x / len(self.testimage_label), hp, lp, hn, ln

    def __generate_report(self, result):
        with open('report.csv', 'a', newline='') as csvfile:
            wr = csv.writer(csvfile, delimiter=',')
            if(os.stat("report.csv").st_size == 0):
                wr.writerow(['PositiveTraining', 'NegativeTraining',
                            'Clustercount', 'contrastThreshold', 'Threshold',
                             'Accuracy', 'HP', 'LP', 'HN', 'LN',
                             'TrainingTime', 'PredictionTime'])
            for threshold in [0.6, 0.7, 0.8]:
                x = []
                for i in result:
                    x.append(i[2] < threshold)
                x = list(map(int, x))
                random_training = sum(self.trainimage_label)
                positive_training = len(self.trainimage_label) - random_training
                row = [positive_training, random_training]
                row.extend([len(self.centroids), self.contrast_threshold, threshold])
                row.extend(self.__score(x))
                row.append(self.trainingtime)
                row.append(self.predictiontime)
                wr.writerow(row)


if __name__ == '__main__':
    dsg = DSG()
    dsg.train()
    result = dsg.predict()
