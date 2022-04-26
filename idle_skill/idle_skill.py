# idle skill (and currently skill manager and conversational skill) for misty
# misty moves her head around, looking for faces, if she finds one, she tries to follow it
# once she sees a face she listens to the "Hey, Misty!" keyword
# after she recognises the keyphrase, she listens to speech
# at the end of speech she attempts to recognise the intent and respond based on that (currently intent recognition is not implemented yet)
# she can also switch skills based on the intent (intent recognition not implemented, but skill switching is working)
# if misty doesn't see a face, she listens to the "Hey, Misty!" keyword
# when she hears it, she starts listening to speech for a few seconds and attempts to turn towards the sound
# some of this skill was based on misty developers' moveToSound and followFace js skills
# moveToSound: https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/moveToSound/moveToSound.js
# followFace: https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/followFace/followFace.js
# misty documentation: https://docs.mistyrobotics.com/

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
import rps
import sys
import stt_bme
import asyncio
import signal
import tts

searching_for_face = None
head_yaw = None
head_pitch = None
yaw_right = None
yaw_left = None
pitch_up = None
pitch_down = None
misty = None
face_rec_event_status = None
seconds_since_last_detection = None
idle_skill = None
date_time_of_last_face_detection = None
testing_skill = True
skill_finished = True
restart_skill = False
start_external = False
skill_to_start = ""
waiting_for_response = False

# move to sound változók
turn_in_progress = False
looked_at = None
robot_yaw = None
head_yaw_for_turning = None
_1b = None
_2b = None
vector = None
degree_list = []

# initializing variables, registering events and starting services required for the idle skill
def init_variables_and_events():
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty, looked_at, robot_yaw, turn_in_progress, _1b, _2b, vector, head_yaw_for_turning, face_rec_event_status
    global date_time_of_last_face_detection, seconds_since_last_detection, idle_skill, skill_finished, restart_skill, start_external, waiting_for_response
    # initializing variables
    idle_skill = True
    restart_skill = False
    start_external = False
    waiting_for_response = False
    # set skill finished False, so the while loop in the main function doesn't keep calling start_idle_skill
    skill_finished = False
    seconds_since_last_detection = 0

    # these are the results of the calibration() function
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

    # starting services
    misty.EnableCameraService()
    #misty.StopFaceRecognition()
    misty.StartFaceRecognition()

    # registering evnets
    # event needed for face recognition
    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function = face_rec_callback, debounce = 1300, keep_alive = True)
    # events needed to store head position data
    misty.RegisterEvent("set_head_yaw", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadYaw], callback_function = set_head_yaw_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("set_head_pitch", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadPitch], callback_function = set_head_pitch_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("heading", Events.IMU, callback_function = heading_callback, debounce = 10, keep_alive = True)
    # events needed for audio localisation and turning
    misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function = sound_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("key_phrase_turn", Events.KeyPhraseRecognized, callback_function = key_phrase_turn_callback, debounce = 10, keep_alive = False)
    # event for bump sensor and cap touch sensor
    misty.RegisterEvent("bump_sensor_pressed", Events.BumpSensor, callback_function = bump_callback, debounce = 10, keep_alive = True)
    misty.RegisterEvent("captouch", Events.TouchSensor, callback_function = captouch_callback, debounce = 100, keep_alive = True)
    misty.StartKeyPhraseRecognition(captureSpeech = False)

# callback for the captouch event
# we use this to restart the idle skill if something goes wrong
def captouch_callback(data):
    global restart_skill
    restart_skill = True
    print("Restarting skill...")
    stop_idle_skill()
    time.sleep(1)

    #start_idle_skill()

# callback for the bump_sensor_pressed event
# currently only used for testing purposes
def bump_callback(data):
    global skill_to_start
    start_external_skill("rps")

# this function stops the idle skill and sets the start_external variable to True
# we call this function when we want to start an external skill from the main loop
# we pass the name of the skill we want to start as a parameter
def start_external_skill(skill = ""):
    global start_external, skill_to_start
    stop_idle_skill()
    time.sleep(1)
    print(f"starting {skill} skill")
    skill_to_start = skill
    start_external = True

# this function starts the idle skill
def start_idle_skill(calibration = False):
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty, looked_at, robot_yaw, turn_in_progress, _1b, _2b, vector, head_yaw_for_turning, face_rec_event_status
    global date_time_of_last_face_detection, seconds_since_last_detection, idle_skill, waiting_for_response
    print("idle_skill STARTED")

    # this is the main loop of the skill
    while idle_skill:
        time.sleep(0.1)
        if misty is not None:
            # if status is not in face_rec_event_status.data it means misty sees a face, so we save the time of the detection
            if not "status" in face_rec_event_status.data:
                date_time_of_last_face_detection = dateutil.parser.isoparse(face_rec_event_status.data["message"]["created"])
            # if we already detected a face, we calculate the seconds since the last detection
            if date_time_of_last_face_detection is not None:
                seconds_since_last_detection = (datetime.now(timezone.utc) - date_time_of_last_face_detection).total_seconds()
            # if the last face detection was more than 4 seconds ago, and turning is not in progress
            # then we unregister events for conversation and register events for turning
            if (seconds_since_last_detection >= 4 or searching_for_face) and not turn_in_progress and not waiting_for_response:
                # if the key_phrase_recognized event is still registered, we stop the KeyPhraseRecognition and unregister the event
                # this is needed, because we need the key_phrase_turn event, and it also uses KeyPhraseRecognition so it conflicts with key_phrase_recognized
                if "key_phrase_recognized" in misty.active_event_registrations:
                    misty.StopKeyPhraseRecognition()
                    time.sleep(1)
                    misty.UnregisterEvent("key_phrase_recognized")
                    print("Face lost...")
                    print("KeyPhraseRecognition stopped (for conversation)")
                # we also unregister voic_cap if it's still registered
                if "voice_cap" in misty.active_event_registrations:
                    misty.UnregisterEvent("voice_cap")
                # if key_phrase_turn is not registered, we register it
                # this event is needed for turning towards sound
                if not "key_phrase_turn" in misty.active_event_registrations:
                    print("KeyPhraseRecognition started (for turning)")
                    misty.StartKeyPhraseRecognition(captureSpeech = False)
                    misty.RegisterEvent("key_phrase_turn", Events.KeyPhraseRecognized, callback_function = key_phrase_turn_callback, debounce = 10, keep_alive = False)
                # if sound is not registered, we register it
                # this event is also needed for turning towards sound
                if not "sound" in misty.active_event_registrations:
                    misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function = sound_callback, debounce = 100, keep_alive = True)
                searching_for_face = True
                # we call the look_side_to_side() function to move Misty's head
                look_side_to_side()
                # we wait so misty can finish moving her head before calling stuff again
                time.sleep(5)
            #print(misty.active_event_registrations)

# calibration function, currently not calling it anywhere, the results are stored in the yaw_right, yaw_left, pitch_down, pitch_up variables
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

# utility function to remove outliers from the voice detection (degreeOfArrivalSpeech) list
def reject_outliers(data, m=6.):
    data = np.array(data)
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / (mdev if mdev else 1.)
    return data[s < m].tolist()

# callback for the heading event
# we recive data from the robot every 10ms, and we store the data in the robot_yaw varaible
def heading_callback(data):
    global robot_yaw
    yaw = data["message"]["yaw"]
    if yaw > 180: yaw -= 360
    robot_yaw = yaw

# callback for the sound event
# this triggers, when an audio recording is started(StartRecordingAudio)
# we store the degrees of arrival speech in the degree_list list
def sound_callback(data):
    global turn_in_progress, _1b, _2b, misty, vector, degree_list

    degree_list.append(data['message']['degreeOfArrivalSpeech'])
    print(data['message']['degreeOfArrivalSpeech'])
    #misty.StopKeyPhraseRecognition()

# callback for the key_phrase_turn event
# this triggers when misty is not looking at a face and she hears "Hey, Misty!"
# we attempt to localise the incoming voice activity and turns towards the sound
def key_phrase_turn_callback(data):
    global turn_in_progress, _1b, _2b, misty, vector, degree_list
    print("key_phrase_turn_callback START")
    turn_in_progress = True
    misty.MoveHead(0, 0, 0, None, 2)
    time.sleep(2)

    # we start recording audio, this is needed for the sound event to trigger
    misty.StartRecordingAudio("deleteThis.wav")
    misty.UnregisterEvent("key_phrase_turn")
    misty.StopKeyPhraseRecognition()
    time.sleep(0.5)
    # we set the LED to green to indicate that misty is listening
    misty.ChangeLED(0, 255, 0)
    misty.DisplayImage("e_Surprise.jpg")
    # we wait a few seconds, continuous speech is required for misty to accurately pick up voice activity
    time.sleep(2)
    misty.ChangeLED(0, 0, 0)
    misty.DisplayImage("e_DefaultContent.jpg")
    # we unregister the sound event and stop the audio recording
    misty.UnregisterEvent("sound")
    misty.StopRecordingAudio()

    # processing the sound data
    degree_list = list(set(degree_list))
    if len(degree_list) > 1:
        # the default value for degreeOfArrivalSpeech is 90, we filter this out if it's not the only element in the list so it doesn't skew the data
        degree_list = list(filter(lambda x: x != 90, degree_list))
    # we also filter out outliers
    degree_list = reject_outliers(degree_list)
    print(degree_list)
    # finally we get the mean of the data, this is our final degree_of_arrival_speech
    degree_of_arrival_speech = mean(degree_list)

    print(f"degree_of_arrival_speech: {degree_of_arrival_speech}")
    degree_list = []
    # if our final result is exactly 90 it is likely that misty didn't pick up the sound (and just sent the default 90), so we don't do anything
    # could also make misty say something
    if degree_of_arrival_speech == 90:
        print("already facing the right direction")
        time.sleep(1)
    else:
        # if the final result is not 90, we call the look_at function
        # the math is taken from the original js script https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/moveToSound/moveToSound.js
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

# utility function needed for the turn calculation
def to_robot_frame(data):
    soundIn = data
    if soundIn > 180 : soundIn -= 360
    return soundIn

# utility function needed for the turn calculation
def offset_heading(to_offset):
	heading = robot_yaw + to_offset
	return (360.0+(heading%360))%360.0

# utility function needed for the turn calculation
def angle_difference(now, to):
    diff = ( to - now + 180 ) % 360 - 180
    return  diff + 360 if diff < -180 else diff

# misty turns towards sound
def look_at(heading, robot_yaw_at_start, head_yaw_at_start):
    global face_rec_event_status, turn_in_progress, looked_at, misty
    print("look_at START")
    look_at_start_time = datetime.now(timezone.utc)
    # we unregister the face_rec event, so misty doesn't look for faces during turning
    misty.UnregisterEvent("face_rec")

    global_heading = offset_heading(heading + (head_yaw_at_start * 2.0))

    if global_heading > 180: global_heading-=360
    # start to turn in place
    misty.Drive(0, 30) if angle_difference(robot_yaw_at_start, global_heading) >= 0 else misty.Drive(0, -30)
    initial_error = abs(angle_difference(robot_yaw_at_start, global_heading))
    current_abs_error = initial_error
    # keep checking if we reached the target heading
    while (abs(robot_yaw - global_heading) >= 3):
        # if misty is turning for more than 10 secs, it is likely that something went wrong
        # e.g robot_yaw - global_heading goes below -3, so abs(robot_yaw - global_heading) >= 3 will always be true
        # so we break and stop misty's turn
        if (datetime.now(timezone.utc) - look_at_start_time).total_seconds() > 10:
            print("something went wrong during turning")
            break
    # when we reach the target, we stop misty's turn
    misty.Stop()
    # after the turning is done, we register the face_rec event again
    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function = face_rec_callback, debounce = 1300, keep_alive = True)
    print("look_at DONE")

# # we call this function, when misty detects a face
# this function registers the voice_cap and key_phrase_recognized events and starts KeyPhraseRecognition
# misty starts listening to "Hey, Misty!" and after the beep sound she is listening to speech, and records it
def start_listening():
    misty.RegisterEvent("voice_cap", Events.VoiceRecord, callback_function = voice_rec_callback, debounce = 10, keep_alive = False)
    misty.RegisterEvent("key_phrase_recognized", Events.KeyPhraseRecognized, callback_function = key_phrase_callback, debounce = 10, keep_alive = False)
    misty.StartKeyPhraseRecognition()
    print("KeyPhraseRecognition started (for conversation)")

# callback for the set_head_yaw event
# stores head position data needed for turning and following face
def set_head_yaw_callback(data):
    global head_yaw, head_yaw_for_turning
    head_yaw = data["message"]["value"]
    head_yaw_local = data["message"]["value"]
    head_yaw_local = -45.0 if head_yaw_local < -45.0 else head_yaw_local
    head_yaw_local = 45.0 if head_yaw_local > 45.0 else head_yaw_local
    head_yaw_for_turning = head_yaw_local
    #print(f"head_yaw set to: {head_yaw}")

# callback for the set_head_pitch event
# stores head position data needed for turning and following face
def set_head_pitch_callback(data):
    global head_pitch
    head_pitch = data["message"]["value"]
    #print(f"head_pitch set to: {head_pitch}")

def key_phrase_callback(data):
    print(f"Misty heard you, trying to wake her up. Confidence: {data['message']['confidence']}%")
    #misty.Speak("Hello")

# this function is supposed to make Misty respond appropriately to the user
# right now intent recognition is not implemented
# if the speech_to_text_result contains "minta" or "mint a" the sample skill starts
# otherwise misty repeats what she heard
def respond(speech_to_text_result = ""):
    global testing_skill, skill_finished, waiting_for_response
    print(speech_to_text_result)

    # TODO: recognise the user's intent and answer or start a skill based on that
    # e.g.
    # if intent == "play rock paper scissors":
    #   start_external_skill("rps")

    if "minta" in speech_to_text_result or "mint a" in speech_to_text_result:
        start_external_skill("sample")
    else:
        tts.synthesize_text_to_robot(misty, speech_to_text_result, "response.wav")

    waiting_for_response = False

# callback for the voice_cap event
# this triggers after we woke misty up with "Hey, Misty!" and started (and finished) speaking to her
# misty captures speech and saves it to the "capture_HeyMisty.wav" file on the Robot
# then we can access this file, send it to STT and call the respond() function
def voice_rec_callback(data):
    global waiting_for_response
    speech_to_text_result = ""
    print("voice_rec_callback START")
    if data["message"]["success"]:
        # accessing the wav file
        encoded_string = misty.GetAudioFile("capture_HeyMisty.wav", True).json()["result"]["base64"]
        misty.DeleteAudio("capture_HeyMisty.wav")
        # copying the file into "out.wav"
        wav_file = open("out.wav", "wb")
        wav_file.write(base64.b64decode(encoded_string))

        # we send the wav file to the BME stt
        try:
            if asyncio.run(stt_api.ws_check_connection()):
                # while we wait for the result, we change the led to green to indicate that stuff is happining in the background
                waiting_for_response = True
                misty.ChangeLED(0, 255, 0)
                res = asyncio.run(stt_api.ws_wav_recognition("out.wav"))
                print("Result: ", res.split(";")[1])
                speech_to_text_result = res.split(";")[1]
            else:
                print("Unable to establish connection to the ASR server!")
        except Exception as e:
            print("ERROR")
            print(e)

        respond(speech_to_text_result)

    else:
        print("Unsuccessful voice recording")
    print("unregistering...")
    #after responding, unregister events needed for the conversation
    if "voice_cap" in misty.active_event_registrations:
        misty.UnregisterEvent("voice_cap")
    if "key_phrase_recognized" in misty.active_event_registrations:
        misty.UnregisterEvent("key_phrase_recognized")
    misty.StopKeyPhraseRecognition()
    time.sleep(1)
    print("voice_rec_callback DONE")


# callback for the face_rec event
# this event triggers when misty sees a face
# in this function we unregister events needed for turning (we want to disable turning while misty sees someone)
# and we register events for conversation (so we can have a conversation or start a skill with speech)
# we also try to follow the recognised face
def face_rec_callback(data):
    global searching_for_face, misty, turn_in_progress

    print("face found!")
    #print(data["message"]["label"])

    # unregistering events used for turning
    if "key_phrase_turn" in misty.active_event_registrations:
        misty.StopKeyPhraseRecognition()
        misty.UnregisterEvent("key_phrase_turn")
        print("key_phrase_turn unregistered")
        misty.Halt()
    if "sound" in misty.active_event_registrations:
        misty.UnregisterEvent("sound")
        print("sound unregistered")
        #respond()

    # we call the start_listening() function, that registers events needed for conversation
    if searching_for_face and not turn_in_progress and not waiting_for_response:
        searching_for_face = False
        #misty.ChangeLED(0, 255, 0);
        misty.DisplayImage("e_Love.jpg")
        time.sleep(1)
        start_listening()

    # if registartion was unsuccessful for some reason (and the conversation events arent registered), we try again
    if not "voice_cap" in misty.active_event_registrations and not "key_phrase_recognized" in misty.active_event_registrations and not turn_in_progress and not waiting_for_response:
        print("first failed")
        start_listening()

    # storing head position data
    bearing = data["message"]["bearing"]
    elevation = data["message"]["elevation"]
    #print(f"bearing: {bearing}")
    #print(f"elevation: {elevation}")

    # misty followes recognised face with her head
    # maths taken from the original skill: https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/followFace/followFace.js
    if bearing != 0 and elevation != 0:
        misty.MoveHead(head_pitch + ((pitch_down - pitch_up) / 33) * elevation, 0, head_yaw + ((yaw_left - yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    elif bearing != 0:
        misty.MoveHead(None, 0, head_yaw + ((yaw_left - yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    else:
        misty.MoveHead(head_pitch + ((pitch_down - pitch_up) / 33) * elevation, 0, None, None, 5 / abs(elevation))

# this function is called when misty doesn't see a face and turning is not in progress
# misty moves her head randomly, trying to find a face
def look_side_to_side():
    print("looking for face...")
    global misty
    misty.DisplayImage("e_DefaultContent.jpg")

    if head_yaw > 0 and not turn_in_progress:
        misty.MoveHead(get_random_int(-20, 0), 0, -40, None, 4)
    elif head_yaw <= 0 and not turn_in_progress:
        misty.MoveHead(get_random_int(-20, 0), 0, 40, None, 4)

# utility function to generate random number between min and max
def get_random_int(min, max):
    return random.randint(min, max)

# this function stops the idle skill
# it unregisters all events, stop any services used in the skill and stops misty's movement
# we call this when we want to switch to a different skill
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
        if(len(sys.argv) > 1):
            misty_ip_address = sys.argv[1]
        else:
            misty_ip_address = "10.2.8.5"
        misty = Robot(misty_ip_address)
        stt_api = stt_bme.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")

        # this loop keeps the program alive
        # if skill_finished is True, we start the idle skill (which sets the skill_finished variable to false)
        # we keep cheking if skill_finished is True, so we can start the idle skill again
        # this is why external skills should return with True when finished
        while True:
            time.sleep(0.1)
            print("main cycle")
            if skill_finished:
                print("starting idle skill")
                init_variables_and_events()
                start_idle_skill()
            if restart_skill:
                print("restarting idle skill")
                init_variables_and_events()
                start_idle_skill()
            # if start_external is True, we check the skill_to_start variable's value and start a skill based on that
            if start_external:
                if skill_to_start == "sample":
                    skill_finished = sample_skill.start_sample_skill(misty)
                if skill_to_start == "rps":
                    skill_finished = rps.start_robot_connection(misty_ip_address)
                else:
                    print("skill not found restarting idle_skill")
                    restart_skill = True


    except Exception as ex:
        print(ex)

    finally:
        # when exiting, stop every running service, unregister events, stop motors
        misty.StopAvStreaming()
        misty.StopFaceRecognition()
        misty.UnregisterAllEvents()
        misty.ChangeLED(0, 0, 0)
        misty.DisplayImage("e_DefaultContent.jpg")
        misty.StopKeyPhraseRecognition()
        misty.StopRecordingAudio()
        misty.Halt()
        print("face rec stopped, unregistered all events")
