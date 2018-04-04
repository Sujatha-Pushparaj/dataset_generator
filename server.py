import http.server as htp
import json
import threading
import os
import configparser
import queue
import test
import shutil
import ipdb
ipdb.set_trace()


class c_handler(htp.BaseHTTPRequestHandler):
    ''' Class that inherits BaseHTTPRequestHandler and handles the get,
    post requests '''
    thread_dict = {}
    thread_ret = queue.Queue()

    def do_GET(self):
        print(self.path)
        print("body:", self.rfile.read())
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        d = {1: 's', 2: 'u'}
        self.wfile.write(json.dumps(d).encode('utf-8'))

    def do_POST(self):
        if(self.path == "/search"):
            print("search is called")
            self.respond_search()
        if(self.path == "/pollsearch"):
            print("pollsearch is called")
            self.pollsearch()
        if(self.path == "/fetchmore"):
            print("fetch more is called")
            self.fetchmore()
        if(self.path == "pollfetchmore"):
            print("pollfetch more is called")
            self.pollfetchmore()
        if(self.path == "/savesetting"):
            print("savesetting is called")
            self.savesetting()

    def respond_search(self):
        # decoding json
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        # initialising all ids
        session_id = json_data['user_id'] + json_data['searchtext']
        config_path = self.create_config(json_data, True)
        job_id = session_id + 'search'
        # initialising & calling thread to download image links
        self.thread_dict[job_id] = threading.Thread(
            target=test.search, args=(self.thread_ret, job_id,
                                      json_data['searchtext'],
                                      'random', json_data['tags_count'],
                                      json_data['image_count'], config_path))
        self.thread_dict[job_id].start()
        # response to client
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        d = {'status': 'processing'}
        self.wfile.write(json.dumps(d).encode('utf-8'))

    def create_config(self, json_data, create=False):
        user_path = os.path.join('./data', json_data['user_id'])
        # create a folder for user
        if not (os.path.exists(user_path)):
            os.makedirs(user_path)
        # create a foler for search item
        search_path = os.path.join(user_path, json_data['searchtext'])
        if not (os.path.exists(search_path)):
            os.makedirs(search_path)
        # create a file for image augmentation if not exists
        augm_set_file_path = os.path.join(search_path, 'config_augm.json')
        if not (os.path.exists(augm_set_file_path)):
            shutil.copy("./image_aug/config_augm.json", search_path)
        config_path = os.path.join(search_path, 'config.ini')
        config = configparser.ConfigParser()
        config.add_section("Details")
        config.set("Details", "last_img_id", "0")
        # writing to a file
        with open(config_path, "w") as config_file:
            config.write(config_file)
        return config_path

    def pollsearch(self):
        # decoding json
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        # initialising ids
        job_id = json_data['user_id'] + json_data['searchtext'] + 'search'
        job_id_dl_train = json_data['user_id'] + json_data['searchtext'] + 'dl_train'
        # building response header
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        try:
            if(self.thread_dict[job_id].isAlive()):
                # job not done
                d = {'status': 'processing'}
                self.wfile.write(json.dumps(d).encode('utf-8'))
            else:
                # job done. send json response
                d = {}
                d['images_det'], d['all_tags'] = self.extract(job_id)
                d['status'] = 'done'
                self.wfile.write(json.dumps(d).encode('utf-8'))
                # create and call a thread to download training images
                self.thread_dict[job_id_dl_train] = threading.Thread(
                    target=test.download_training_images,
                    args=(json_data['user_id'], json_data['searchtext'],
                          d['images_det']))
                self.thread_dict[job_id_dl_train].start()
        except Exception as e:
            print(e)

    def extract(self, job_id):
        q_size = self.thread_ret.qsize()
        for i in range(q_size):
            value = self.thread_ret.get()
            # if key matches job, return the value
            if(list(value.keys()) == [job_id]):
                print("found")
                return value[job_id]
            # else enqueue back the element
            self.thread_ret.put(value)

    def fetchmore(self):
        # decoding json
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        print(json_data)
        # initialising all ids
        session_id = json_data['user_id'] + json_data['searchtext']
        job_id_train = session_id + 'download_train'
        job_id_dl_train = json_data['user_id'] + json_data['searchtext'] + 'dl_train'
        job_id_fetch = session_id + 'download_predict_img'
        config_path = self.create_config(json_data)
        # thread for training images
        self.thread_dict[job_id_train] = threading.Thread(
            target=test.train,
            args=(self.thread_ret, json_data['user_id'],
                  json_data['searchtext'], json_data['sel_images'],
                  self.thread_dict[job_id_dl_train]))
        # thread for fetching more images for prediction
        self.thread_dict[job_id_fetch] = threading.Thread(
            target=test.download_for_prediction,
            args=(self.thread_ret, json_data['user_id'],
                  json_data['searchtext'], json_data['sel_tags'],
                  int(json_data['images_count']),
                  config_path))
        # starting threads for training and fetching images parallely
        self.thread_dict[job_id_train].start()
        self.thread_dict[job_id_fetch].start()
        # sending response to client
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        d = {'status': 'processing'}
        self.wfile.write(json.dumps(d).encode('utf-8'))

    def pollfetchmore(self):
        # decode json
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        # initialising ids
        job_id = json_data['user_id'] + json_data['searchtext'] + 'fetchmore'
        # send response to client
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        try:
            if(self.thread_dict[job_id].isAlive()):
                d = {'status': 'processing'}
                self.wfile.write(json.dumps(d).encode('utf-8'))
            else:
                d = {}
                d['images_det'] = self.extract(job_id)
                d['status'] = 'done'
                self.wfile.write(json.dumps(d).encode('utf-8'))
        except Exception as e:
            print(e)

    def savesetting(self):
        # decoding json
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        search_path = os.path.join('./data', json_data['user_id'],
                                   json_data['searchtext'])
        if not (os.path.exists(search_path)):
            os.makedirs(search_path)
        augm_set_file_path = os.path.join(search_path, 'config_augm.json')
        with open(augm_set_file_path, 'w') as outfile:
            json.dump(json_data['settings'], outfile)
        # send response to client
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        d = {'status': 'saved'}
        self.wfile.write(json.dumps(d).encode('utf-8'))


server = htp.HTTPServer
ser = server(('192.168.1.168', 8080), c_handler)
ser.serve_forever()
