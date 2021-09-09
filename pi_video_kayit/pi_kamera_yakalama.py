
from tempimage.tempimage import TempImage

import datetime as dt
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import dropbox
import imutils
import json
import time
import cv2
import datetime


ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
args = vars(ap.parse_args())

warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None


#dbx = dropbox.Dropbox('sl.AwmbbvuAIqS8tUhm_Ei-ojHrhUxDle0RgV9zFyKpyOsRhKLwsjlyePKXVpMvA1i-wEUewvaTC9dl8NpUSE0-ZVhT81Vg1fiWm06P1XSdVcYW8a5WTdPrlAA1WVuqRzz1ioKUczo')

# check to see if the Dropbox should be used
#if conf["use_dropbox"]:
	# connect to dropbox and start the session authorization process
	#client = dropbox.Dropbox("sl.AwmbbvuAIqS8tUhm_Ei-ojHrhUxDle0RgV9zFyKpyOsRhKLwsjlyePKXVpMvA1i")
	#print("[SUCCESS] dropbox account linked")


camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

        
print("[Bilgi] Makine isniyor...")
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0

for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	
	frame = f.array
	timestamp = datetime.datetime.now()
	text = "algilanmadi"
	
	frame = imutils.resize(frame, width=500)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)
	
	if avg is None:
		print("[Bilgi] Arkaplan modeli baslatiliyor...")
		avg = gray.copy().astype("float")
		rawCapture.truncate(0)
		continue
	
	
	cv2.accumulateWeighted(gray, avg, 0.5)
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
	
	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
		cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=2)
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	
	for c in cnts:
		
		if cv2.contourArea(c) < conf["min_area"]:
			continue
		
		
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "algilandi"
	
	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)
	
	if text == "algilandi":
		#a = videodetect()
        
		if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
			
			motionCounter += 1
			
			if motionCounter >= conf["min_motion_frames"]:
				
				if conf["use_dropbox"]:
					
					t = TempImage()
					
					cv2.imwrite(t.path, frame)					
					print("[Yüklendi] {}".format(ts))
					
			
				
				
				lastUploaded = timestamp
				motionCounter = 0
				
	
	else:
		motionCounter = 0
	
	if conf["show_video"]:
		
		cv2.imshow("Security Feed", frame)
		key = cv2.waitKey(1) & 0xFF
		
		
		if key == ord("q"):
            #camera.stop_recording()
			break
	
	
	rawCapture.truncate(0)