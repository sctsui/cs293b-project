# Code adapted from Tensorflow Object Detection Framework
# https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
# Tensorflow Object Detection Detector
import os
import numpy as np
import tensorflow as tf
import cv2
import time
#import tensorflow.compat.v1 as tf
#tf.disable_v2_behavior()



class DetectorAPI:
    def __init__(self, path_to_ckpt):
        self.path_to_ckpt = path_to_ckpt

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self.path_to_ckpt, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        self.default_graph = self.detection_graph.as_default()
        self.sess = tf.Session(graph=self.detection_graph)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

    def processFrame(self, image):
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image, axis=0)
        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_np_expanded})
        end_time = time.time()

        #print("Elapsed Time:", end_time-start_time)

        im_height, im_width,_ = image.shape
        boxes_list = [None for i in range(boxes.shape[1])]
        for i in range(boxes.shape[1]):
            boxes_list[i] = (int(boxes[0,i,0] * im_height),
                        int(boxes[0,i,1]*im_width),
                        int(boxes[0,i,2] * im_height),
                        int(boxes[0,i,3]*im_width))

        return boxes_list, scores[0].tolist(), [int(x) for x in classes[0].tolist()], int(num[0])

    def close(self):
        self.sess.close()
        self.default_graph.close()

if __name__ == "__main__":
    model_path = '/home/ubuntu/faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb'
    odapi = DetectorAPI(path_to_ckpt=model_path)
    threshold = 0.7
    humanCountThreshold = 5
    x_dim = 160
    y_dim = 90
    videos_path = "/home/ubuntu/videos/combined/"
    filenames = os.listdir(videos_path)
    fileCount = 1
    out_file = open("out_file_" + str(x_dim) + "_" + str(y_dim) + ".txt", "a")
    time_list = []
    for filename in filenames:
        start_time = time.perf_counter()
        print(str(fileCount)+" : Started processing for "+filename)
        #fileCount = fileCount + 1
        cap = cv2.VideoCapture(videos_path+filename)
        #cap.set(cv2.CAP_PROP_FPS, 2)
        humanCount = 0
        fileCount = fileCount+1
        while True:
            r, img = cap.read()
            if r==False:
                out_file.write(filename + " : 0\n")
                print("Human not found in "+filename)
                end_time = time.perf_counter()
                print(end_time - start_time)
                out_file.write(str(end_time - start_time) + "\n")
                time_list.append(end_time - start_time)
                break
            img = cv2.resize(img, (x_dim, y_dim))
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # img = cv2.resize(img, (480, 320))
            boxes, scores, classes, num = odapi.processFrame(img)

            # Visualization of the results of a detection.

            for i in range(len(boxes)):
                # Class 1 represents human
                if classes[i] == 1 and scores[i] > threshold:
                    box = boxes[i]
                    humanCount = humanCount+1

            #cv2.imshow("preview", img)
            if humanCount > humanCountThreshold:
                out_file.write(filename + " : 1\n")
                print("Human found in "+filename)
                end_time = time.perf_counter()
                print(end_time - start_time)
                time_list.append(end_time - start_time)
                out_file.write(str(end_time - start_time) + "\n")
                # Invoke alert script here
                break
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break
    time_list = np.array(time_list)
    out_file.write("Mean:" + "\t" + str(np.mean(time_list)) + "\n")
    out_file.write("Max:" + "\t" + str(np.max(time_list)) + "\n")
    out_file.write("Min:" + "\t" + str(np.min(time_list)) + "\n")
    out_file.write("Total:" + "\t" + str(np.sum(time_list)) + "\n")
    out_file.write("Done")
    out_file.close()

