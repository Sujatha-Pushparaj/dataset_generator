import http.server as htp
import json
import threading
import queue
import test


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

    def respond_search(self):
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        print(json_data)
        job_id = json_data['user_id'] + json_data['searchtext']
        print(job_id)
        self.thread_dict[job_id] = threading.Thread(
            target=test.search, args=(self.thread_ret, job_id,
                                      json_data['searchtext'],
                                      'random', json_data['tags_count'],
                                      json_data['image_count']))
        self.thread_dict[job_id].start()
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        d = {'status': 'processing'}
        self.wfile.write(json.dumps(d).encode('utf-8'))

    def pollsearch(self):
        content_len = int(self.headers['Content-Length'])
        byte_data = self.rfile.read(content_len)
        json_data = json.loads(byte_data.decode('utf8').replace("'", '"'))
        print(json_data)
        job_id = json_data['user_id'] + json_data['searchtext']
        self.send_response(200)
        self.send_header('Content-type', "JSON")
        self.end_headers()
        try:
            if(self.thread_dict[job_id].isAlive()):
                d = {'status': 'processing'}
                self.wfile.write(json.dumps(d).encode('utf-8'))
            else:
                d = self.extract(job_id)
                print(d)
                d['status'] = 'done'
                self.wfile.write(json.dumps(d).encode('utf-8'))
        except Exception as e:
            print(e)

    def extract(self, job_id):
        q_size = self.thread_ret.qsize()
        print("queue size:%d job_id:%s" %(q_size, job_id))
        for i in range(q_size):
            value = self.thread_ret.get()
            print(list(value.keys()), list(job_id))
            if(list(value.keys()) == [job_id]):
                print("found")
                return value[job_id]
            self.thread_ret.put(value)


server = htp.HTTPServer
ser = server(('192.168.1.168', 8080), c_handler)
ser.serve_forever()
