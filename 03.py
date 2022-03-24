import ffmpeg
import numpy as np
import subprocess
import cv2

from time import gmtime, strftime

# https://stackoverflow.com/questions/70813361/how-to-extract-video-and-audio-from-ffmpeg-stream-in-python
# https://github.com/kkroening/ffmpeg-python/blob/master/examples/tensorflow_stream.py

stream_uri = "rtsp://10.2.8.5:1936"
width = 640
height = 480

def start_ffmpeg_video_process(input_uri):
    args = (
        ffmpeg
        .input(input_uri, format='rawvideo', pix_fmt='rgb24')
        .output('pipe:', format='rawvideo', pix_fmt='rgb24')
        .compile()
    )
    return subprocess.Popen(args, stdout=subprocess.PIPE)

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

def process_frame(frame):
    print(frame)

process = start_ffmpeg_video_process(stream_uri)

while True:
    print("Reading frame.")
    in_frame = read_video_frame(process, width, height)
    if in_frame is None:
        break
    
    process_frame(in_frame)

