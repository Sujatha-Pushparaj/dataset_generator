# importing required libraries
import json
import shutil
import time
import random

import Augmentor
import cv2
import os
import numpy as np
from keras.preprocessing.image import ImageDataGenerator
from keras import backend as K


def salt_and_pepper_noise(image, probability=0.5, magnitude=0.004):
  '''
  Salt and Pepper Noise
  Input : Image, probability to add noise, magnitude of the noise
  Output: Noise image 
  '''
  # generating a random number for checking the probability
  if probability > random.random():
    # the ratio of salt noise
    s_vs_p = 0.5
    out = np.copy(image)
    # Salt mode
    num_salt = np.ceil(magnitude * image.size * s_vs_p)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in image.shape]
    out[coords] = 1
    # Pepper mode
    num_pepper = np.ceil(magnitude * image.size * (1 - s_vs_p))
    coords = [np.random.randint(0, i - 1, int(num_pepper))
             for i in image.shape]
    out[coords] = 0
    sp_img = out
  else:
  	sp_img = image
  return sp_img


def vignetting(img, probability=0.5, px=0.25, py=0.25):
  '''
  Vignetting
  Input : Image, probability to add noise, percentage of rows , percentage of columns
  Output : Vignetted Image
  '''
  # generating a random number for checking the probability
  if (probability > random.random()):
  	rows, cols = img.shape[:2]
  	# generating vignette mask using Gaussian kernels
  	kernel_x = cv2.getGaussianKernel(cols, cols * px)
  	kernel_y = cv2.getGaussianKernel(rows, rows * py)
  	kernel = kernel_y * kernel_x.T
  	mask = ((rows+cols)//6) * kernel / np.linalg.norm(kernel)
  	output = np.copy(img)
  	# applying the mask to each channel in the input image
  	for i in range(3):
  	  output[:, :, i] = output[:, :, i] * mask
  	v_img = output
  else:
  	v_img = img
  return v_img


def color_shift(img_process, probability=0.5, color_shift_range=50):
  '''
  Color Shift
  Input : Image, Probability of the function to be execuited, maximum colors
  Output : color shifted image
  '''
  #selecting the required operations in keras lib
  gen = ImageDataGenerator(channel_shift_range=color_shift_range,
  	data_format=K.image_data_format())
  #expanding the dimension so that the keras lib can process a single image
  img_process1 = np.expand_dims(img_process, axis=0)
  #generating a random number for checking the probability
  if probability > random.random():
  	img_process2 = gen.flow(img_process1)
  	img_process3 = [next(img_process2)[0].astype(np.uint8)]
  	images = img_process3[0]
  else:
  	images = img_process1[0]
  images = np.array(images, dtype='uint8')
  return images


def possible_functions(data):
  '''
  Possible Functions
  Input : Json file data
  Output : Possible functions, probability that functions can be selected
  '''
  #funcutions that user has enabled
  enables = [
            data["params"]["flip_left_right"]["enable"]["value"][0],
            data["params"]["flip_random"]["enable"]["value"][0],
            data["params"]["flip_top_bottom"]["enable"]["value"][0],
            data["params"]["gaussian_distortion"]["enable"]["value"][0],
            data["params"]["random_distortion"]["enable"]["value"][0],
            data["params"]["random_erasing"]["enable"]["value"][0],
            data["params"]["rotate_without_crop"]["enable"]["value"][0],
            data["params"]["shear"]["enable"]["value"][0],
            data["params"]["skew"]["enable"]["value"][0],
            data["params"]["skew_corner"]["enable"]["value"][0],
            data["params"]["skew_left_right"]["enable"]["value"][0],
            data["params"]["skew_tilt"]["enable"]["value"][0],
            data["params"]["skew_top_bottom"]["enable"]["value"][0],
            data["params"]["zoom"]["enable"]["value"][0],
            data["params"]["zoom_random"]["enable"]["value"][0],
            data["params"]["vignetting"]["enable"]["value"][0],
            data["params"]["salt_and_pepper_noise"]["enable"]["value"][0],
            data["params"]["color_shift"]["enable"]["value"][0]
            ]
  #the probability that the user has specified for each function
  probabilities = [
                  data["params"]["flip_left_right"]["probability"]["value"][0],
                  data["params"]["flip_random"]["probability"]["value"][0],
                  data["params"]["flip_top_bottom"]["probability"]["value"][0],
                  data["params"]["gaussian_distortion"]["probability"]["value"][0],
                  data["params"]["random_distortion"]["probability"]["value"][0],
                  data["params"]["random_erasing"]["probability"]["value"][0],
                  data["params"]["rotate_without_crop"]["probability"]["value"][0],
                  data["params"]["shear"]["probability"]["value"][0],
                  data["params"]["skew"]["probability"]["value"][0],
                  data["params"]["skew_corner"]["probability"]["value"][0],
                  data["params"]["skew_left_right"]["probability"]["value"][0],
                  data["params"]["skew_tilt"]["probability"]["value"][0],
                  data["params"]["skew_top_bottom"]["probability"]["value"][0],
                  data["params"]["zoom"]["probability"]["value"][0],
                  data["params"]["zoom_random"]["probability"]["value"][0],
                  data["params"]["vignetting"]["probability"]["value"][0],
                  data["params"]["salt_and_pepper_noise"]["probability"]["value"][0],
                  data["params"]["color_shift"]["probability"]["value"][0]
                  ]
  #name of all the functions
  functions = [
              "flip_left_right",
              "flip_random",
              "flip_top_bottom",
              "gaussian_distortion",
              "random_distortion",
              "random_erasing",
              "rotate_without_crop",
              "shear",
              "skew",	
              "skew_corner",
              "skew_left_right",
              "skew_tilt",
              "skew_top_bottom",
              "zoom",	
              "zoom_random",
              "vignetting",
              "salt_and_pepper_noise",
              "color_shift",
              ]
  possible = []
  probability = []
  #sorting the functions and its probability that user has enabled
  for item, pro, enable in zip(functions, probabilities, enables):
  	if enable:
  	  possible.append(item)		#possible Functions
  	  probability.append(pro)	#functions respective probability
  #calculating the total probabilty to 1
  pro_sum = sum(probability)
  cal_probability = map(lambda x: x/pro_sum, probability)
  possible = list(possible)
  cal_probability = list(cal_probability)
  return possible, cal_probability


def function_selection(data, possible, probability, image_no, localtime):
  '''
  Functions Selection
  Input : Data from Json file calculated, probability, image number, local time
  Output : Processed image, name of the image 
  '''
  #initializing the image to be agumented
  p = Augmentor.Pipeline("./%s"%localtime)
  #random selection of number of agumentation to be performed with in specified limit
  ran = random.randint(1, data["general"]["no_of_agu"]["value"][0])
  #selecting the functions randomly based on the given probability
  sel_fun = np.random.choice(possible, ran, replace=False, p=probability)
  #performing the selected functions
  names = [image_no]
  #performing the augmentor lib functions
  if "flip_left_right" in sel_fun:
  	p.flip_left_right(probability=1)
  	names.append("f_l_r")
  if "flip_random" in sel_fun:
  	p.flip_random(probability=1)
  	names.append("f_r")
  if "flip_top_bottom" in sel_fun:
  	p.flip_top_bottom(probability=1)
  	names.append("f_t_b")
  if "gaussian_distortion" in sel_fun:
  	p.gaussian_distortion(probability=1,
  		                  grid_width=data["params"]["gaussian_distortion"]["grid_width"]["value"][0],
  		                  grid_height=data["params"]["gaussian_distortion"]["grid_height"]["value"][0],
  		                  magnitude=data["params"]["gaussian_distortion"]["magnitude"]["value"][0],
  		                  corner="bell", method="in", mex=0.5, mey=0.5,
  		                  sdx=0.05, sdy=0.05
  		                  )
  	names.append("g_d")
  if "random_distortion" in sel_fun:
  	p.random_distortion(probability=1,
  		                grid_width=data["params"]["random_distortion"]["grid_width"]["value"][0],
  		                grid_height=data["params"]["random_distortion"]["grid_height"]["value"][0],
  		                magnitude=data["params"]["random_distortion"]["magnitude"]["value"][0]
  		                )
  	names.append("r_d")
  if "random_erasing" in sel_fun:
  	p.random_erasing(probability=1,
  		             rectangle_area=data["params"]["random_erasing"]["rectangle_area"]["value"][0]
  		             )
  	names.append("r_e")
  if "rotate_without_crop" in sel_fun:
  	p.rotate_without_crop(probability=1,
  		                  max_left_rotation=data["params"]["rotate_without_crop"]["max_left_rotation"]["value"][0],
  		                  max_right_rotation=data["params"]["rotate_without_crop"]["max_right_rotation"]["value"][0],
  		                  expand=False
  		                  )
  	names.append("r_w_c")
  if "shear" in sel_fun:
  	p.shear(probability=1,
  		    max_shear_left=data["params"]["shear"]["max_shear_left"]["value"][0],
  		    max_shear_right = data["params"]["shear"]["max_shear_right"]["value"][0]
  		    )
  	names.append("sh")
  if "skew" in sel_fun:
  	p.skew(probability=1, magnitude=data["params"]["skew"]["magnitude"]["value"][0])
  	names.append("sk")
  if "skew_corner" in sel_fun:
  	p.skew_corner(probability=1, magnitude=data["params"]["skew_corner"]["magnitude"]["value"][0])
  	names.append("sk_c")
  if "skew_left_right" in sel_fun:
  	p.skew_left_right(probability=1,
  		              magnitude=data["params"]["skew_left_right"]["magnitude"]["value"][0]
  		              )
  	names.append("sk_l_r")
  if "skew_tilt" in sel_fun:
  	p.skew_tilt(probability=1, magnitude=data["params"]["skew_tilt"]["magnitude"]["value"][0])
  	names.append("sk_t")
  if "skew_top_bottom" in sel_fun:
  	p.skew_top_bottom(probability=1,
  		              magnitude=data["params"]["skew_top_bottom"]["magnitude"]["value"][0]
  		              )
  	names.append("sk_t_b")
  if "zoom" in sel_fun:
  	p.zoom(probability=1,
  		   min_factor=data["params"]["zoom"]["min_factor"]["value"][0],
  		   max_factor = data["params"]["zoom"]["max_factor"]["value"][0]
  		   )
  	names.append("z")
  if "zoom_random" in sel_fun:
  	p.zoom_random(probability=1,
  		          percentage_area=data["params"]["zoom_random"]["percentage_area"]["value"][0],
  		          randomise_percentage_area=False
  		          )
  	names.append("z_r")
  #converting the image to useable formate for other lib
  batch_images = p.keras_generator(batch_size=1, scaled=True,
  	                               image_data_format=u'channels_last'
  	                               )
  batch_images1, labels = next(batch_images)
  batch_images1 = batch_images1[0] * 255
  #functions of the cv lib are performed
  if "vignetting" in sel_fun:
  	batch_images1 = vignetting(batch_images1, probability=1,
  		                       px=data["params"]["vignetting"]["px"]["value"][0],
  		                       py=data["params"]["vignetting"]["py"]["value"][0]
  		                       )
  	names.append("v")
  if "salt_and_pepper_noise" in sel_fun:
  	batch_images1=salt_and_pepper_noise(batch_images1, probability=1,
  	                                    magnitude=data["params"]["salt_and_pepper_noise"]["magnitude"]["value"][0]
  	                                    )
  	names.append("s_a_p_n")
  #functions of the keras lib is performed
  if "color_shift" in sel_fun:
  	batch_images1 = color_shift(batch_images1, probability=1,
  	                            color_shift_range=data["params"]["color_shift"]["magnitude"]["value"][0]
  	                            )
  	names.append("c_s")
  #converting image into wirtable formate
  image = np.array(batch_images1, dtype='uint8')
  image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
  name = "__".join(names)
  return image , name


def agu_img(image, data, batch_size=100, image_no="1"):
  '''
  Agumenting single image
  Input : Image to be agumented, data from the Json file, 
          number of output images to be produced, image number
  Output : list of processed images with its names
  '''
  #creating a temaporary directory and saving the image there so to be used by agumentor
  localtime = "_".join(time.asctime( time.localtime(time.time())).split(" "))
  os.mkdir("./%s"%localtime)
  cv2.imwrite("./%s/image.png"%localtime, image)
  processed = []
  names =[]
  #calling the possible functions to get the enabled functions with its probability
  possible, probability = possible_functions(data)
  #iterating the functions so that to agument a image in different ways
  for x in range(batch_size):
  	image, name = function_selection(data, possible, probability, image_no, localtime)
  	names.append(name)
  	processed.append(image)
  #deleting the temparory folder created
  shutil.rmtree("./%s"%localtime, ignore_errors=True)
  return processed ,names


def agu_mul_img(images , data , total_batch_size) :
  '''
  Agumenting multiple images
  Input : list of images to be agumented , data from Json file,
           total number of output images
  Output : list of agumented images with its names
  '''
  #calculating batch size for each image
  com = total_batch_size // len(images)
  rem = total_batch_size % len(images)
  batch_sizes = [com] * len(images)
  if rem != 0 :
  	batch_sizes[0 : (rem-1)] = [com + 1] * rem
  batch_images = []
  batch_names = []
  image_no = 1
  #calling the single image agumentation for each image
  for image, batch_size in zip(images, batch_sizes):
  	processed, names = agu_img(image, data, batch_size,
  		                       image_no="__".join(["img", str(image_no)]))
  	image_no = image_no + 1
  	batch_images.append(processed)
  	batch_names.append(names)
  processed_img = [img for batch in batch_images for img in batch]
  processed_nam = [nam for batch in batch_names for nam in batch]
  return processed_img, processed_nam


def test_single_image_agu ():
  '''
  test function for single image agumentation
  '''
  json_file_path = "./config_agum.json"
  batch_size = 200
  img = "./images/img1.jpeg"
  image = cv2.imread(img)
  #open the json file and and storing the data
  with open(json_file_path,'r') as json_file:
  	data = json.load(json_file)
  	json_file.close()
  processed, names = agu_img(image, data, batch_size)
  if not os.path.isdir("./output"):
  	os.mkdir("./output")
  for x, image  in enumerate(processed):
  	cv2.imwrite('./output/%s__%s.png'%(names[x], x), image)

	
def test_mul_image_agu(dir_path, batch_size=100):
  '''
  test function for multiple image agumentation
  '''
  json_file_path = "./image_aug/config_augm.json"
  # dir_path = "./images"
  path_images = [os.path.join(dir_path, f) for f in os.listdir(dir_path)
                 if os.path.isfile(os.path.join(dir_path, f))]
  total_batch_size = batch_size
  images = []
  #open the json file and and storing the data
  with open(json_file_path, 'r') as json_file:
  	data = json.load(json_file)
  	json_file.close()
  for path in path_images:
  	images.append(cv2.imread(path))
  batch_images, batch_names = agu_mul_img(images, data, total_batch_size)
  #if not os.path.isdir("./output"):
  	#os.mkdir("./output")
  for x, image in enumerate(batch_images):
    path = dir_path+'/%s__%s.png'%(batch_names[x], x)
    cv2.imwrite(path, image)

#test_mul_image_agu()
#test_single_image_agu()