import ffmpeg
import numpy as np
import subprocess
import cv2

from time import gmtime, strftime

import struct

# https://stackoverflow.com/questions/70813361/how-to-extract-video-and-audio-from-ffmpeg-stream-in-python
# https://github.com/kkroening/ffmpeg-python/blob/master/examples/tensorflow_stream.py

# "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4" -teszt stream
stream_uri = "rtsp://10.2.8.5:1936"
width = 640
height = 480

def start_ffmpeg_video_process(input_uri):
    args = (
        ffmpeg
        .input(input_uri, r = 30) # r-nek bármit megadva működik
        .output('pipe:', format='rawvideo', pix_fmt='bgr24')
        .compile()
    )
    return subprocess.Popen(args, stdout=subprocess.PIPE)

def start_ffmpeg_audio_process(input_uri):
    args = (
        ffmpeg
        .input(stream_uri)
        .output('pipe:', format='s16le', ar=44100)
        .compile()
    )
    return subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=100)

def read_video_frame(process, width, height):
    frame_size = width * height * 3
    in_bytes = process.stdout.read(frame_size)
    if len(in_bytes) == 0:
        frame = None
    else:
        assert len(in_bytes) == frame_size
        frame = (
            np
            .frombuffer(in_bytes, np.uint8)
            .reshape([height, width, 3])
        )
    return frame

def read_audio(process):
    byte_str = process.stdout.read(4)
    num, = struct.unpack('<i', byte_str)
    return num

def process_frame(frame):
    #print(frame)
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    cv2.imshow('video', frame)
    cv2.waitKey(1)

process_v = start_ffmpeg_video_process(stream_uri)
process_a = start_ffmpeg_audio_process(stream_uri)

print("start")

while True:
    print("Reading frame.")
    in_frame = read_video_frame(process_v, width, height)
    if in_frame is None:
       break

    process_frame(in_frame)
    print("Frame")
    print(int(read_audio(process_a)))
