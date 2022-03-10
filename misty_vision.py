import cv2
import time

avstream_connected = False

while (avstream_connected == False):
    try:
        #vcap = cv2.VideoCapture("rtsp://10.2.8.5:1936", cv2.CAP_FFMPEG)
        vcap = cv2.VideoCapture(0)
        avstream_connected = True
    except:
        print("Stream is not available")
        time.sleep(1)

while(1):
    ret, frame = vcap.read()
    if ret == False:
        print("Frame is empty")
        break
    else:
        image = cv2.rotate(frame, cv2.cv2.ROTATE_90_CLOCKWISE)
        cv2.imshow('VIDEO', image)
        cv2.waitKey(1)

vcap.release()
cv2.destroyAllWindows()
