#!/usr/local/bin/python3

from tempimage.tempimage.py import tempimage 
import argparse
import warnings
import datetime
import imutils
import json
import numpy as np
import os
import time
import cv2

print("[Bilgi] Baslatiliyor - " +
      datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))


ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
                help="path to the JSON configuration file")
args = vars(ap.parse_args())


warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))


if not conf["use_ip_cam"]:
    camera = cv2.VideoCapture(1)
    time.sleep(0.25)


else:
    camera = cv2.VideoCapture(conf["ip_cam_addr"])


print("[Bilgi] Makine isiniyor...")
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motion_counter = 0
non_motion_timer = conf["nonMotionTimer"]
fourcc = 0x00000020  
writer = None
(h, w) = (None, None)
zeros = None
output = None
made_recording = False


while True:
    
    (grabbed, frame) = camera.read()

    timestamp = datetime.datetime.now()
    motion_detected = False

    if not grabbed:
        print("[Bilgi] Cerceve Yakalanamadi - " +
              datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))
        break

    
    frame = imutils.resize(frame, width=conf["resizeWidth"])
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    
    if avg is None:
        print("[Bilgi] Arkaplan Modeli Baslatiliyor...")
        avg = gray.copy().astype("float")
#         frame.truncate(0)
        continue

    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    
    _, threshold = cv2.threshold(frameDelta, 3, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

        

    for c in contours:
       
        if cv2.contourArea(c) < conf["min_area"]:
            continue

        (x, y, w1, h1) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w1, y + h1), (0, 255, 255), 2)
        motion_detected = True

    fps = int(round(camera.get(cv2.CAP_PROP_FPS)))
    record_fps = 10
    ts = timestamp.strftime("%Y-%m-%d_%H_%M_%S")
    time_and_fps = ts + " - fps: " + str(fps)

    
    cv2.putText(frame, "Algilandi: {}".format(motion_detected), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(frame, time_and_fps, (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35, (0, 0, 255), 1)

    
    if writer is None:
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        
        file_path = (conf["userDir"] +
                     "/{filename}.mp4")
        file_path = file_path.format(filename=filename)
        

        (h2, w2) = frame.shape[:2]
        writer = cv2.VideoWriter(file_path, fourcc, record_fps, (w2, h2), True)
        zeros = np.zeros((h2, w2), dtype="uint8")

    def record_video():
       
        output = np.zeros((h2, w2, 3), dtype="uint8")
        output[0:h2, 0:w2] = frame

        
        writer.write(output)
        print("[Hata Ayıklama] Kayit....")

    if motion_detected:

        
        motion_counter += 1

        
        if motion_counter >= conf["min_motion_frames"]:
            if conf["create_image"]:
                
                image_path = (conf["userDir"] + 
                              "/{filename}.jpg").format(filename=filename)
                cv2.imwrite(image_path, frame)
                
                

            record_video()

            made_recording = True
            non_motion_timer = conf["nonMotionTimer"]

  
    else:  
        print("[Hata] Hareket Yok")
        if made_recording is True and non_motion_timer > 0:
            non_motion_timer -= 1
            print("[Hata] first else and timer: " + str(non_motion_timer))
            record_video()
        else:
            
            motion_counter = 0
            if writer is not None:
                print("[Hata] 1 ise çalıştır")
                writer.release()
                writer = None
            if made_recording is False:
                print("[Hata] 2 ise çalıştır ")
                os.remove(file_path)
            made_recording = False
            non_motion_timer = conf["nonMotionTimer"]

  
    if conf["show_video"]:
        cv2.imshow("Güvenlik", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key is pressed, break from the loop
        if key == ord("q"):
            break


print("[Bilgi] Temizleniyor...")
camera.release()
cv2.destroyAllWindows()