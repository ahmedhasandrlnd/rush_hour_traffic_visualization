import argparse
import cv2
import sys
import numpy as np
import socket
import json
import paho.mqtt.client as mqtt
from random import randint
from inference import Network

INPUT_STREAM = "Autonomous.mp4"
CPU_EXTENSION = "/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so"
ADAS_MODEL = "/home/workspace/models/person-vehicle-bike-detection-crossroad-0078.xml"

CLASSES = ['road', 'sidewalk', 'building', 'wall', 'fence', 'pole', 
'traffic_light', 'traffic_sign', 'vegetation', 'terrain', 'sky', 'person',
'rider', 'car', 'truck', 'bus', 'train', 'motorcycle', 'bicycle', 'ego-vehicle']

# MQTT server environment variables
HOSTNAME = socket.gethostname()
IPADDRESS = socket.gethostbyname(HOSTNAME)
MQTT_HOST = IPADDRESS
MQTT_PORT = 3001
MQTT_KEEPALIVE_INTERVAL = 60

def get_args():
    '''
    Gets the arguments from the command line.
    '''
    parser = argparse.ArgumentParser("Run inference on an input video")
    # -- Create the descriptions for the commands
    i_desc = "The location of the input file"
    d_desc = "The device name, if not 'CPU'"
    cv_desc = "The confidence threshold to use with the bounding boxes for vehicles"
    cp_desc = "The confidence threshold to use with the bounding boxes for people"
    cb_desc = "The confidence threshold to use with the bounding boxes for bikes"

    # -- Create the arguments
    parser.add_argument("-i", help=i_desc, default=INPUT_STREAM)
    parser.add_argument("-d", help=d_desc, default='CPU')
    parser.add_argument("-cv", help=cv_desc, default=0.5)
    parser.add_argument("-cp", help=cp_desc, default=0.5)
    parser.add_argument("-cb", help=cb_desc, default=0.5)    
    args = parser.parse_args()

    return args


def draw_masks(result, width, height):
    '''
    Draw semantic mask classes onto the frame.
    '''
    # Create a mask with color by class
    classes = cv2.resize(result[0].transpose((1,2,0)), (width,height), 
        interpolation=cv2.INTER_NEAREST)
    unique_classes = np.unique(classes)
    out_mask = classes * (255/20)
    
    # Stack the mask so FFmpeg understands it
    out_mask = np.dstack((out_mask, out_mask, out_mask))
    out_mask = np.uint8(out_mask)

    return out_mask, unique_classes
def draw_boxes(frame, result,args, width, height):
    '''
    Draw bounding boxes onto the frame.
    '''
    #class_array={ "1": "person", "2": "bicycle", "3": "car","4": "motorcycle","5": "airplane","6": "bus", "7": "train","8": "truck","9": "boat","10":"traffic light"}
    vehicles=[]
    people_count=0
    bike_count=0
    for box in result[0][0]: # Output shape is 1x1x100x7
        conf = box[2]
        box_class=int(box[1])
        #class_obj=class_array.get(str(box[1]))
        #print(str(box[1]))
        if conf >= float(args.cv) and box_class==2:
            xmin = int(box[3] * width)
            ymin = int(box[4] * height)
            xmax = int(box[5] * width)
            ymax = int(box[6] * height)
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255,0,255), 2)
            cv2.putText(frame,"Vehicle",(xmin,ymin),cv2.FONT_HERSHEY_DUPLEX , 1, (255,0,255))
            vehicles.append(box_class)
        if conf >= float(args.cp) and box_class==1:
            xmin = int(box[3] * width)
            ymin = int(box[4] * height)
            xmax = int(box[5] * width)
            ymax = int(box[6] * height)
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255,0,0), 2)
            cv2.putText(frame,"People",(xmin,ymin),cv2.FONT_HERSHEY_DUPLEX , 1, (255,0,0))
            people_count+=1
        if conf >= float(args.cb) and box_class==3:
            xmin = int(box[3] * width)
            ymin = int(box[4] * height)
            xmax = int(box[5] * width)
            ymax = int(box[6] * height)
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255,0,0), 2)
            cv2.putText(frame,"Bike",(xmin,ymin),cv2.FONT_HERSHEY_DUPLEX , 1, (255,0,0))
            bike_count+=1
            people_count+=1

    return frame,vehicles,people_count,bike_count

def get_class_names(class_nums):
    class_names= []
    for i in class_nums:
        class_names.append(CLASSES[int(i)])
    return class_names


def infer_on_video(args, model):
    ### TODO: Connect to the MQTT server
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

    # Initialize the Inference Engine
    plugin = Network()

    # Load the network model into the IE
    plugin.load_model(model, args.d, CPU_EXTENSION)
    net_input_shape = plugin.get_input_shape()

    # Get and open video capture
    cap = cv2.VideoCapture(args.i)
    cap.open(args.i)

    # Grab the shape of the input 
    width = int(cap.get(3))
    height = int(cap.get(4))
    
    # Create a video writer for the output video
    # The second argument should be `cv2.VideoWriter_fourcc('M','J','P','G')`
    # on Mac, and `0x00000021` on Linux
    out = cv2.VideoWriter('out.mp4', 0x00000021, 30, (width,height))

    # Process frames until the video ends, or process is exited
    while cap.isOpened():
        # Read the next frame
        flag, frame = cap.read()
        if not flag:
            break
        key_pressed = cv2.waitKey(60)

        # Pre-process the frame
        p_frame = cv2.resize(frame, (net_input_shape[3], net_input_shape[2]))
        p_frame = p_frame.transpose((2,0,1))
        p_frame = p_frame.reshape(1, *p_frame.shape)

        # Perform inference on the frame
        plugin.async_inference(p_frame)

        # Get the output of inference
        if plugin.wait() == 0:
            result = plugin.extract_output()
            # Draw the output mask onto the input
            out_frame,classes,people_count,bike_count = draw_boxes(frame, result,args, width, height)
            class_names = get_class_names(classes)
            speed = people_count
            speed1 = bike_count
            
            ### TODO: Send the class names and speed to the MQTT server
            ### Hint: The UI web server will check for a "class" and
            ### "speedometer" topic. Additionally, it expects "class_names"
            ### and "speed" as the json keys of the data, respectively.
            client.publish("class", json.dumps({"class_names": class_names}))
            client.publish("speedometer", json.dumps({"speed": speed}))
            client.publish("speedometer1", json.dumps({"speed1": speed1}))

        # Write out the frame
        out.write(out_frame)
        
        ### TODO: Send frame to the ffmpeg server
        sys.stdout.buffer.write(out_frame)
        sys.stdout.flush()

        # Break if escape key pressed
        if key_pressed == 27:
            break

    # Release the capture and destroy any OpenCV windows
    cap.release()
    cv2.destroyAllWindows()
    ### TODO: Disconnect from MQTT
    client.disconnect()


def main():
    args = get_args()
    model = ADAS_MODEL
    infer_on_video(args, model)


if __name__ == "__main__":
    main()
