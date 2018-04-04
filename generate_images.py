import json
import os
import time

import urllib.request
from selenium import webdriver
import urllib

os.environ["PATH"] += os.pathsep + os.getcwd()  #for  geckodrive
all_tags =[]

def open_browser():
  ''' 
  Process : to initate the browser and to open
  '''
  driver = webdriver.Firefox()
  return driver


def close_browser(driver):
  '''
  Process : to close the browser
  '''
  driver.quit()

def find_tags(s):
  '''
  Process : to find all tags and store it in a list
  '''
  tags = [None]
  while(True):
    start = s.find('<div class="ZO5Spb">')
    if start == -1:
      break
    start_obj = s.find('data-ident="',start) + 12
    end_obj = s.find('"',start_obj)
    tag = s[start_obj:end_obj]
    tags.append(tag)
    s = s[end_obj:]
  return tags


def get_all_tags(searchtext = "car"):
  '''
  Process : to open the url and to fetch all tags
  '''
  searchtext = "+".join(searchtext.strip().split(" "))
  url = "https://www.google.co.in/search?q="+searchtext+"&source=lnms&tbm=isch"
  try:
   headers = {}
   headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
   req = urllib.request.Request(url, headers=headers)
   resp = urllib.request.urlopen(req)
   respData = str(resp.read())
   tags = find_tags(respData)
  except Exception as e:
    print(str(e))
  return tags


def fetch_links(driver, searchtext="car", start=0, count_argv=10, tags = None, extensions=[]):
  '''
  Process : to get links for number of images to be downloaded 
  Input : the browser address, search phrase, count to be downloaded, download path, tag of the image to be download
  Output : list of dictonaries so that it contains all the information of the image
  '''
  num_requested = int(count_argv) + int(start)
  #to decide the number of scrolls to be done. 1 scroll loads 20 images
  number_of_scrolls = num_requested / 20 + 1
  #for the purpose of url building and for naming the directory
  if not tags:
    tag = ""
    tags = ""
  else:
    tag = tags
    tags = "&chips=q:%s,%s"%("+".join(searchtext.split(" ")),"+".join(tags.split(" ")))
  #building the url
  url = "https://www.google.co.in/search?q=%s&source=lnms&tbm=isch%s"%("+".join(searchtext.split(" ")),tags)
  #opening the url in the browser
  driver.get(url)
  #scrolling to the required level so that to extract the links of the images to be downloaded
  for _ in range(int(number_of_scrolls)):
    #each iteration scrolls for around 20 images
    for _ in range(1):
      driver.execute_script("window.scrollBy(0, 1000)")
      #time delay for each scroll
      #time.sleep(0.1)
    #time to load all 20 images
    #time.sleep(0.1)
    #try to search wheather there is any show more results button if so click
    try:
      driver.find_element_by_xpath("//input[@value='Show more results']").click()
    except Exception as e:
      print ("Less images found:", e)
      break
  #finding all the details of the image that is to be download
  images = driver.find_elements_by_xpath('//div[contains(@class,"rg_meta")]')
  valid_images = []
  for i in images:
    img_type = json.loads(i.get_attribute('innerHTML'))["ity"]
    if(img_type in extensions):
      # appends the url of the image
      valid_images.append((json.loads(i.get_attribute('innerHTML'))["ou"],img_type))
  valid_images = valid_images[start:start+count_argv]
  print ("Total images:", len(valid_images), "\n")
  return valid_images


def download_img(driver, download_path, images_det):
  #for the purpose of url building and for naming the directory
  headers = {}
  headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
  #creating the folder for tags if not exist
  if not (os.path.exists(download_path)):
        os.makedirs(download_path)
  #downloading the images
  for x, img in enumerate(images_det):
    #reading the image url and its type
    print('************',download_path)
    img_url = img['url']
    img_id = img['ID']
    img_type = img['type']
    try:
      #creating a file to store the image
      f = open(download_path + '/' + img_id + '.' + img_type, "wb")
      #requesting the response from from the url and downloading the raw data and storing it
      req = urllib.request.Request(img_url, headers=headers)
      timeout = 1
      raw_img = urllib.request.urlopen(req, timeout = 1).read()
      print("download count : %s \nurl : %s"%(img_id, img_url))
      f.write(raw_img)
      f.close
    except Exception as e:
      print ("Download failed:", e)
      os.remove(download_path + '/' + img_id + '.' + img_type)

def download_img1(driver, searchtext="car", start=0, count_argv=10, download_path="./download", tags = None,images = [], img_urls=[]):
  #for the purpose of url building and for naming the directory
  if not tags:
    tag = ""
    tags = ""
  else:
    tag = tags
    tags = "&chips=q:%s,%s"%("+".join(searchtext.split(" ")),"+".join(tags.split(" ")))
  #the extentions to be allowed
  headers = {}
  headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
  #images that are downloaded will be stored here for further details
  if not tag:
    searchtext = "_".join(searchtext.split(" "))
  else:
    searchtext = "_".join(["_".join(searchtext.split(" ")) , tag.split(":")[1]])
  #creating directory if not present
  if not os.path.exists(download_path + "/" + searchtext.replace(" ", "_")):
    os.makedirs(download_path + "/" + searchtext.replace(" ", "_"))
  #downloading the images
  count = 1
  for img_url in img_urls:
    try:
      #creating a file to store the image
      f = open(download_path+"/"+searchtext.replace(" ", "_")+"/"+searchtext.replace(" ", "_")+str(count + start)+"."+img_type, "wb")
      #requesting the response from from the url and downloading the raw data and storing it
      req = urllib.request.Request(img_url, headers=headers)
      timeout = 1
      raw_img = urllib.request.urlopen(req, timeout = 1).read()
      print("download count : %s \nurl : %s"%(count, img_url))
      f.write(raw_img)
      f.close
      count = count + 1
    except Exception as e:
      print ("Download failed:", e)
      fail_count += 1
      if(type(e)=='socket.timeout'):
        print('************')
        timeout_count += 1
      os.remove(download_path+"/"+searchtext.replace(" ", "_")+"/"+searchtext.replace(" ", "_")+str(count + start)+"."+img_type)
      #count = count - 1
    if count_argv < count :
      break
  if count_argv > count:
    #checking weather the images count specified is satisfied or not
    print ("Less number of images found please enter different search phrase or tag")
  print("total downloads : %s fail couunt :%s timeout :%s"%(count-1, fail_count, timeout_count))


def mul_tags(driver,searchtext, download_path="./download", all_tags=[None], tag_list=[0], start_list=[0], count_list=[100]):
  image_links = {}
  extensions = ["jpg", "jpeg", "png"]
  for i, tag_no in enumerate(tag_list):
    images = fetch_links(driver, searchtext=searchtext, start=start_list[i], count_argv=count_list[i], download_path=download_path, tags = all_tags[tag_no], extensions=extensions)
    image_links[all_tags[tag_no]] = download_img(driver, searchtext=searchtext, start=start_list[i], count_argv=count_list[i], download_path=download_path, tags = all_tags[tag_no],images = images)
    #image_links[all_tags[tag_no]] = images
  return image_links

def get_links(driver,searchtext, all_tags=[None], tag_list=[0], start_list=[0], count_list=[100], last_img_id=0):
  extensions = ["jpg", "jpeg", "png"]
  images_det = []
  for i, tag_no in enumerate(tag_list):
    image_links_types = fetch_links(driver, searchtext=searchtext, start=start_list[i], count_argv=count_list[i], tags = all_tags[tag_no], extensions=extensions)
    for a_image in image_links_types:
      last_img_id += 1
      image_det = {"ID": str(last_img_id) ,"tag": all_tags[tag_no],"url":a_image[0], "type":a_image[1]}
      images_det.append(image_det)
  return images_det, str(last_img_id)

def download_images_for_prediction(driver,searchtext, download_path="./download", all_tags=[None], tag_list=[0], start_list=[0], count_list=[100], last_img_id=0):
  extensions = ["jpg", "jpeg", "png"]
  for i, tag in enumerate(all_tags):
    if tag is None:
      tag = "None"
    images_det=[]
    tag_path = os.path.join(download_path, tag)
    image_links_types = fetch_links(driver, searchtext=searchtext, start=start_list[i], count_argv=count_list[i], tags = tag, extensions=extensions)
    for a_image in image_links_types:
      last_img_id += 1
      image_det = {"ID": str(last_img_id) ,"tag": tag,"url":a_image[0], "type":a_image[1]}
      images_det.append(image_det)
    download_img(driver, tag_path, images_det)
    remove_corrupt_images.remove()
  return str(last_img_id)

'''
def generate_image(searchtext, tagscount, download_path):
  
  enable the below to execuite this functions

  searchtext = "computer"
  all_tags = get_all_tags(searchtext = searchtext)[:tagscount]
  driver = open_browser()
  #images = fetch_links(driver, searchtext="car", start=100, count_argv=10, download_path="./download", tags = None)
  #download_img(driver, searchtext="car", start=100, count_argv=10, download_path="./download", tags = None,images = images)
  tag_list = [i for i in range(0, len(all_tags))]
  start_list = [0] * len(all_tags)
  count_list = [10] * len(all_tags)
  mul_tags(driver,searchtext=searchtext,download_path=download_path,all_tags=all_tags,tag_list=tag_list,start_list=start_list,count_list=count_list)
  close_browser(driver)

#generate_image('car', 5, "./images/training/positive")
#generate_image('headset', 5, "images/training/negative") '''