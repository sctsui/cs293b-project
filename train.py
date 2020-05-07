import cv2
from keras.preprocessing import image
import os
import argparse
import numpy as np
from sklearn.model_selection import train_test_split
from keras.layers import LSTM
from keras.models import Sequential
from keras.layers.convolutional import Conv2D
from keras.layers.core import Dropout
from keras.layers.core import Dense

def parse_cmd_line():
  parser = argparse.ArgumentParser(add_help=False)
  parser.add_argument('--path', type=str, default=None)
  parser.add_argument('--extract', type=int, default=1)
  args = parser.parse_args()
  if args.path:
    if not os.path.isdir(args.path):
      print("Your --path does not represent a valid directory. Aborting.")
      return [False, args.path, args.extract]
  if (args.extract != 0) & (args.extract != 1):
    print("Please use either 0 or 1 for the --extract argument. Aborting.")
    return [False, args.path, args.extract]
  return [True, args.path, args.extract]

def check_create_dirs(outer_dir, inner_dir):
    if not os.path.exists(outer_dir):
        os.makedirs(outer_dir)
    if not os.path.exists(outer_dir + "/" + inner_dir):
        os.makedirs(outer_dir + "/" + inner_dir)

def generate_filepath(writefile_prefix, directory, frame_number):
    return directory + "/" + writefile_prefix[:-4] + "/" + writefile_prefix[:-4] + "_%d.png" % frame_number

def extract_frames(readfile, writefile_prefix, directory, num_frames_to_save=15, resize=True, x_dim=224, y_dim=224):
    video = cv2.VideoCapture(readfile)
    num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT) # Get number of frames in video
    if num_frames < num_frames_to_save: # Reject if not enough frames
      print("File \"" + readfile + "\" has only " + str(num_frames) + " frames. Discarding.")
      return
    factor = num_frames//num_frames_to_save
    success, image = video.read()
    frame_number = 0
    num_frames_saved = 0
    check_create_dirs(directory, writefile_prefix[:-4])
    while success:
      if (frame_number%factor) == 0:
        # Resize and write image
        if resize:
          image = cv2.resize(image, (x_dim, y_dim))
        cv2.imwrite(generate_filepath(writefile_prefix, directory, frame_number), image)
        num_frames_saved += 1
        # Check if we have saved enough frames
        if num_frames_saved == num_frames_to_save:
          return
      # Get next frame
      success, image = video.read()
      frame_number += 1
    return

def extract_frames_all(read_directory_name, write_directory_name):
  for filename in os.listdir(read_directory_name):
    extract_frames(read_directory_name + "/" + filename, filename, write_directory_name)

def read_training_data(base_directory_name, training_set, labels, contains_humans = True, num_sets_to_read = None):
  num_sets_read = 0
  for directory in os.listdir(base_directory_name):
    frames_of_video = []
    for filename in os.listdir(base_directory_name + "/" + directory):
      train_image = image.load_img(base_directory_name + "/" + directory + "/" + filename, target_size=(224,224,3))
      train_image = image.img_to_array(train_image)
      train_image = train_image/255
      train_image = train_image.flatten()
      frames_of_video.append(train_image)
    if contains_humans:
      labels.append([1,0])
    else:
      labels.append([0,1])
    training_set.append(frames_of_video)
    num_sets_read += 1
    if num_sets_to_read:
      if num_sets_to_read == num_sets_read:
        print(str(num_sets_read) + " videos have been read.")
        return
  print(str(num_sets_read) + " videos have been read.")
  return

def get_data_and_labels(directory_1="contains_human_extracted", directory_2="human_less_extracted"):
  training_set = []
  labels = []
  read_training_data(directory_1, training_set, labels, True, 5)
  read_training_data(directory_2, training_set, labels, False, 5)
  full_data_set = np.array(training_set)
  (x_train, x_test, y_train, y_test) = train_test_split(full_data_set, labels, test_size=0.25, stratify=labels, random_state=42)
  x_train = np.array(x_train)
  y_train = np.array(y_train)
  x_test = np.array(x_test)
  y_test = np.array(y_test)
  return (x_train, x_test, y_train, y_test)

def get_model():
  model = Sequential()
  model.add(LSTM(100, input_shape=(15, 224*224*3)))
  model.add(Dropout(0.5))
  model.add(Dense(100, activation='relu'))
  model.add(Dense(2, activation='softmax'))
  model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
  return model

if __name__ == '__main__':
  [status, path, perform_extraction] = parse_cmd_line()
  if status:
    if path:
      os.chdir(path)
    if perform_extraction == 1:
      extract_frames_all("contains_human", "contains_human_extracted")
      extract_frames_all("human_less", "human_less_extracted")
      print("Video frames successfully extracted.")
    (x_train, x_test, y_train, y_test) = get_data_and_labels()
    print("Train and test data read.")
    lstm_model = get_model()
    print("Model generated.")
    lstm_model.fit(x_train, y_train, epochs=5, validation_data=(x_test, y_test))
    print("Training complete.")
