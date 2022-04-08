from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters
import random
import time
from datetime import datetime, timezone
import dateutil.parser
import base64
import stt
import numpy as np
from statistics import mean
import operator
import sample_skill
import robot_main

searching_for_face = None
head_yaw = None
head_pitch = None
yaw_right = None
yaw_left = None
pitch_up = None
pitch_down = None
misty = None
first_contact = None
face_rec_event_status = None
seconds_since_last_detection = None
idle_skill = None
time_of_last_face_detection = None
date_time_of_last_face_detection = None
testing_skill = True
skill_finished = True

# move to sound változók
turn_in_progress = False
looked_at = None
robot_yaw = None
head_yaw_for_turning = None
_1b = None
_2b = None
vector = None
degree_list = []

def init_variables_and_events():
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty, looked_at, robot_yaw, turn_in_progress, _1b, _2b, vector, head_yaw_for_turning, face_rec_event_status
    global time_of_last_face_detection, date_time_of_last_face_detection, seconds_since_last_detection, idle_skill, skill_finished

    idle_skill = True
    skill_finished = False
    seconds_since_last_detection = 0

    yaw_right = -85.94366926962348
    yaw_left = 80.21409131831524
    pitch_down = 26.35605857601787
    pitch_up = -33.231552117587746

    misty.MoveHead(0, 0, 0, None, 1)
    searching_for_face = True
    misty.ChangeLED(0, 0, 0)
    head_yaw = 0.0
    head_yaw_for_turning = 0.0
    head_pitch = 0.0
    robot_yaw = 0.0
    _1b = 0.0
    _2b = 0.0
    vector = 0.0
    looked_at = datetime.now(timezone.utc)

    #misty.StartRecordingAudio("deleteThis.wav")
    misty.EnableCameraService()
    misty.StopFaceRecognition()
    misty.StartFaceRecognition()

    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function = face_rec_callback, debounce = 1300, keep_alive = True)
    misty.RegisterEvent("set_head_yaw", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadYaw], callback_function = set_head_yaw_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("set_head_pitch", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadPitch], callback_function = set_head_pitch_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("heading", Events.IMU, callback_function = heading_callback, debounce = 10, keep_alive = True)
    misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function = sound_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("key_phrase_turn", Events.KeyPhraseRecognized, callback_function = key_phrase_turn_callback, debounce = 10, keep_alive = False)
    misty.RegisterEvent("bump_sensor_pressed", Events.BumpSensor, callback_function = bump_callback, debounce = 10, keep_alive = True)
    misty.StartKeyPhraseRecognition(captureSpeech = False)


def bump_callback(data):
    global skill_finished
    stop_idle_skill()
    time.sleep(1)
    #skill_finished = robot_main.start_robot_connection("10.2.8.5")
    skill_finished = sample_skill.start_sample_skill(misty)

def start_idle_skill(calibration = False):
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty, looked_at, robot_yaw, turn_in_progress, _1b, _2b, vector, head_yaw_for_turning, face_rec_event_status
    global time_of_last_face_detection, date_time_of_last_face_detection, seconds_since_last_detection
    print("idle_skill STARTED")
    init_variables_and_events()

    while idle_skill:
        #print(turn_in_progress
        #print(misty.active_event_registrations)
        if not "status" in face_rec_event_status.data:
            time_of_last_face_detection = face_rec_event_status.data["message"]["created"]
            date_time_of_last_face_detection = dateutil.parser.isoparse(time_of_last_face_detection)
        now = datetime.now(timezone.utc)
        if date_time_of_last_face_detection is not None:
            seconds_since_last_detection = (now - date_time_of_last_face_detection).total_seconds()
        if (seconds_since_last_detection >= 4 or searching_for_face) and not turn_in_progress:
            if "key_phrase_recognized" in misty.active_event_registrations:
                misty.StopKeyPhraseRecognition()
                time.sleep(1)
                misty.UnregisterEvent("key_phrase_recognized")
                print("Face lost...")
                print("KeyPhraseRecognition stopped (for conversation)")
            if "voice_cap" in misty.active_event_registrations:
                misty.UnregisterEvent("voice_cap")
            if not "key_phrase_turn" in misty.active_event_registrations:
                print("KeyPhraseRecognition started (for turning)")
                misty.StartKeyPhraseRecognition(captureSpeech = False)
                misty.RegisterEvent("key_phrase_turn", Events.KeyPhraseRecognized, callback_function = key_phrase_turn_callback, debounce = 10, keep_alive = False)
            if not "sound" in misty.active_event_registrations:
                misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function = sound_callback, debounce = 100, keep_alive = True)
            searching_for_face = True
            look_side_to_side()
            time.sleep(6.5)
            #print(misty.active_event_registrations)
    #misty.KeepAlive()

def calibrate():
    global yaw_right, yaw_left, pitch_down, pitch_up
    print("CALIBRATION STARTED")
    misty.MoveHead(0, 0, -90, None, 2)
    time.sleep(4)
    yaw_right = head_yaw
    print(f"yaw_right recorded: {yaw_right}")

    misty.MoveHead(0, 0, 90, None, 2);
    time.sleep(4)
    yaw_left = head_yaw
    print(f"yaw_left recorded: {yaw_left}")

    misty.MoveHead(90, 0, 0, None, 2)
    time.sleep(4)
    pitch_down = head_pitch
    print(f"pitch_down recorded: {pitch_down}")

    misty.MoveHead(-90, 0, 0, None, 2)
    time.sleep(4)
    pitch_up = head_pitch
    print(f"pitch_up recorded: {pitch_up}")

    print("CALIBRATION COMPLETE")
    misty.MoveHead(0, 0, 0, None, 2)

def reject_outliers(data, m=6.):
    data = np.array(data)
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / (mdev if mdev else 1.)
    return data[s < m].tolist()

def heading_callback(data):
    global robot_yaw
    yaw = data["message"]["yaw"]
    if yaw > 180: yaw -= 360
    robot_yaw = yaw

def sound_callback(data):
    global turn_in_progress, _1b, _2b, misty, vector, degree_list
    #voice_activity = data['message']['voiceActivityPolar']
    #degree_dict = { i+1 : lst[i] for i in range(0, len(lst) ) }
    #max_key = max(op.items(), key=operator.itemgetter(1))[0]
    #degree_list.append(max_key)

    degree_list.append(data['message']['degreeOfArrivalSpeech'])
    print(data['message']['degreeOfArrivalSpeech'])
    #misty.StopKeyPhraseRecognition()

def key_phrase_turn_callback(data):
    global turn_in_progress, _1b, _2b, misty, vector, degree_list
    print("key_phrase_turn_callback START")
    turn_in_progress = True
    misty.MoveHead(0, 0, 0, None, 2)
    time.sleep(2)

    misty.StartRecordingAudio("deleteThis.wav")
    misty.UnregisterEvent("key_phrase_turn")
    misty.StopKeyPhraseRecognition()
    time.sleep(0.5)
    misty.ChangeLED(0, 255, 0)
    misty.DisplayImage("e_Surprise.jpg")

    time.sleep(2)
    misty.ChangeLED(0, 0, 0)
    misty.DisplayImage("e_DefaultContent.jpg")

    misty.UnregisterEvent("sound")
    misty.StopRecordingAudio()

    #degree_list = list(filter(lambda x: x != 90 and x != 180, degree_list))
    #print(degree_list)
    #degree_of_arrival_speech = mean(degree_list)
    degree_list = list(set(degree_list))
    if len(degree_list) > 1:
        degree_list = list(filter(lambda x: x != 90, degree_list))
    degree_list = reject_outliers(degree_list)

    print(degree_list)
    degree_of_arrival_speech = mean(degree_list)

    print(f"degree_of_arrival_speech: {degree_of_arrival_speech}")
    degree_list = []
    if degree_of_arrival_speech == 90:
        print("already facing the right direction")
        time.sleep(1)
    else:
        vector = 0.4 * to_robot_frame(degree_of_arrival_speech) + 0.35 * _1b + 0.25 * _2b
        #if seconds_past(looked_at) > 5.0 and searching_for_face:
        print("Misty hallott, fordul a hang felé...")
        print(f"vector: {vector}")
        #turn_in_progress = True
        #print(f"{vector} <-- Look At Input Global")
        look_at(vector, robot_yaw, head_yaw_for_turning)
        misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function = sound_callback, debounce = 100, keep_alive = True)
        _2b = _1b
        _1b = vector
    turn_in_progress = False
    print("key_phrase_callback DONE")

def to_robot_frame(data):
    soundIn = data
    if soundIn > 180 : soundIn -= 360
    return soundIn

def seconds_past(value):
    timeElapsed = (datetime.now(timezone.utc) - value).total_seconds()
    return timeElapsed

def offset_heading(to_offset):
	heading = robot_yaw + to_offset
	return (360.0+(heading%360))%360.0

def angle_difference(now, to):
    diff = ( to - now + 180 ) % 360 - 180
    return  diff + 360 if diff < -180 else diff

def look_at(heading, robot_yaw_at_start, head_yaw_at_start):
    global face_rec_event_status
    print("look_at START")
    look_at_start_time = datetime.now(timezone.utc)
    global turn_in_progress, looked_at, misty
    misty.UnregisterEvent("face_rec")

    global_heading = offset_heading(heading + (head_yaw_at_start * 2.0))

    if global_heading > 180: global_heading-=360
    misty.Drive(0, 30) if angle_difference(robot_yaw_at_start, global_heading) >= 0 else misty.Drive(0, -30)
    #print(f"{global_heading} <- Body to move to")
    initial_error = abs(angle_difference(robot_yaw_at_start, global_heading))
    current_abs_error = initial_error
    #print(f"global_heading: {global_heading}")
    #print(f"robot_yaw: {robot_yaw}")
    while (abs(robot_yaw - global_heading) >= 3):
        #print(f"robot_yaw - global_heading = {robot_yaw} - {global_heading} = {robot_yaw - global_heading}")
        if (datetime.now(timezone.utc) - look_at_start_time).total_seconds() > 10:
            print("something went wrong during turning")
            break
    misty.Stop()

    looked_at = datetime.now(timezone.utc)
    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function = face_rec_callback, debounce = 1300, keep_alive = True)
    print("look_at DONE")

def start_listening():
    global first_contact
    first_contact = True
    misty.RegisterEvent("voice_cap", Events.VoiceRecord, callback_function = voice_rec_callback, debounce = 10, keep_alive = False)
    misty.RegisterEvent("key_phrase_recognized", Events.KeyPhraseRecognized, callback_function = key_phrase_callback, debounce = 10, keep_alive = False)
    misty.StartKeyPhraseRecognition()
    print("KeyPhraseRecognition started (for conversation)")

def set_head_yaw_callback(data):
    global head_yaw, head_yaw_for_turning
    head_yaw = data["message"]["value"]
    head_yaw_local = data["message"]["value"]
    head_yaw_local = -45.0 if head_yaw_local < -45.0 else head_yaw_local
    head_yaw_local = 45.0 if head_yaw_local > 45.0 else head_yaw_local
    head_yaw_for_turning = head_yaw_local
    #print(f"head_yaw set to: {head_yaw}")

def set_head_pitch_callback(data):
    global head_pitch
    head_pitch = data["message"]["value"]
    #print(f"head_pitch set to: {head_pitch}")

def key_phrase_callback(data):
    print(f"Misty heard you, trying to wake her up. Confidence: {data['message']['confidence']}%")
    #misty.Speak("Hello")

def respond():
    global testing_skill, skill_finished
    # TODO: feldolgozni a beérkezett beszédet, választ küldeni
    print("OK")
    if testing_skill:
        stop_idle_skill()
        skill_finished = sample_skill.start_sample_skill(misty)

def voice_rec_callback(data):
    print("voice_rec_callback START")
    if data["message"]["success"]:
        encoded_string = misty.GetAudioFile("capture_HeyMisty.wav", True).json()["result"]["base64"]
        misty.DeleteAudio("capture_HeyMisty.wav")
        wav_file = open("out.wav", "wb")
        wav_file.write(base64.b64decode(encoded_string))
        print("speech to text starts")
        txt = stt.speech_to_text("out.wav")
        print(f"{txt}")
        print("recording finished")
        # valami függvény ami feldolgozza a hangot + válaszol
        if txt != "":
            respond() # placeholder válasz
        else:
            misty.Speak("Sorry, I didn't catch that.")
        #misty.StartKeyPhraseRecognition()
    else:
        print("Unsuccessful voice recording")
    print("unregistering...")
    if "voice_cap" in misty.active_event_registrations:
        misty.UnregisterEvent("voice_cap")
    if "key_phrase_recognized" in misty.active_event_registrations:
        misty.UnregisterEvent("key_phrase_recognized")
    misty.StopKeyPhraseRecognition()
    time.sleep(1)
    print("voice_rec_callback DONE")

def face_rec_callback(data):
    global searching_for_face, misty, turn_in_progress

    print("face found!")
    #print(data["message"]["label"])

    if "key_phrase_turn" in misty.active_event_registrations:
        misty.StopKeyPhraseRecognition()
        misty.UnregisterEvent("key_phrase_turn")
        print("key_phrase_turn unregistered")
        time.sleep(1)
    if "sound" in misty.active_event_registrations:
        misty.UnregisterEvent("sound")
        print("sound unregistered")
        #respond()

    if searching_for_face and not turn_in_progress:
        searching_for_face = False
        #misty.ChangeLED(0, 255, 0);
        misty.DisplayImage("e_Love.jpg")
        start_listening()

    if not "voice_cap" in misty.active_event_registrations and not "key_phrase_recognized" in misty.active_event_registrations and not turn_in_progress:
        start_listening()

    bearing = data["message"]["bearing"]
    elevation = data["message"]["elevation"]
    #print(f"bearing: {bearing}")
    #print(f"elevation: {elevation}")

    if bearing != 0 and elevation != 0:
        misty.MoveHead(head_pitch + ((pitch_down - pitch_up) / 33) * elevation, 0, head_yaw + ((yaw_left - yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    elif bearing != 0:
        misty.MoveHead(None, 0, head_yaw + ((yaw_left - yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    else:
        misty.MoveHead(head_pitch + ((pitch_down - pitch_up) / 33) * elevation, 0, None, None, 5 / abs(elevation))

def look_side_to_side():
    print("looking for face...")
    global misty
    misty.DisplayImage("e_DefaultContent.jpg")

    if head_yaw > 0 and not turn_in_progress:
        misty.MoveHead(get_random_int(-20, 0), 0, -40, None, 4)
    elif head_yaw <= 0 and not turn_in_progress:
        misty.MoveHead(get_random_int(-20, 0), 0, 40, None, 4)

def get_random_int(min, max):
    return random.randint(min, max)

def stop_idle_skill():
    #misty.MoveHead(0, 0, 0, None, 2)
    global idle_skill
    idle_skill = False
    misty.StopFaceRecognition()
    misty.UnregisterAllEvents()
    #misty.ChangeLED(255, 255, 255)
    misty.DisplayImage("e_DefaultContent.jpg")
    misty.StopKeyPhraseRecognition()
    misty.StopRecordingAudio()
    misty.Halt()
    print("IDLE_SKILL_STOPPED")

    return

if __name__ == "__main__":
    try:
        ip_address = "10.2.8.5"
        misty = Robot(ip_address)
        print(ip_address)
        #misty.Speak("Hello")

        while True:
            if skill_finished:
                print("starting idle skill")
                start_idle_skill()

    except Exception as ex:
        print(ex)

    finally:
        misty.StopAvStreaming()
        misty.StopFaceRecognition()
        misty.UnregisterAllEvents()
        misty.ChangeLED(0, 0, 0)
        misty.DisplayImage("e_DefaultContent.jpg")
        misty.StopKeyPhraseRecognition()
        misty.StopRecordingAudio()
        misty.Halt()
        print("face rec stopped, unregistered all events")
