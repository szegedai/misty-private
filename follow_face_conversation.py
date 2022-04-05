from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters
import random
import time
from datetime import datetime, timezone
import dateutil.parser
import base64
import stt

searching_for_face = None
head_yaw = None
head_pitch = None
yaw_right = None
yaw_left = None
pitch_up = None
pitch_down = None
misty = None
first_contact = None
responded = False
skill_running = True

def start_face_following_skill(calibration = False):
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty
    face_rec_event_status = None
    time_of_last_face_detection = None
    date_time_of_last_face_detection = None
    seconds_since_last_detection = 0
    print("start_face_following_skill elindult")

    misty.MoveHead(0, 0, 0, None, 1)
    searching_for_face = True
    misty.ChangeLED(255, 255, 255)
    head_yaw = 0.0
    head_pitch = 0.0

    misty.RegisterEvent("set_head_yaw", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadYaw], callback_function = set_head_yaw_callback, debounce = 100, keep_alive = True)
    misty.RegisterEvent("set_head_pitch", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadPitch], callback_function = set_head_pitch_callback, debounce = 100, keep_alive = True)

    if calibration:
        calibrate()
    else:
        yaw_right = -85.94366926962348
        yaw_left = 80.21409131831524
        pitch_down = 26.35605857601787
        pitch_up = -33.231552117587746

    misty.StopFaceRecognition()
    misty.StartFaceRecognition()

    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function = face_rec_callback, debounce = 1300, keep_alive = True)

    while skill_running:
        if not "status" in face_rec_event_status.data:
            time_of_last_face_detection = face_rec_event_status.data["message"]["created"]
            date_time_of_last_face_detection = dateutil.parser.isoparse(time_of_last_face_detection)
        now = datetime.now(timezone.utc)
        if date_time_of_last_face_detection is not None:
            seconds_since_last_detection = (now - date_time_of_last_face_detection).total_seconds()
        if seconds_since_last_detection >= 4 or searching_for_face:
            searching_for_face = True
            if "voice_cap" in misty.active_event_registrations:
                misty.UnregisterEvent("voice_cap")
            if "key_phrase_recognized" in misty.active_event_registrations:
                misty.UnregisterEvent("key_phrase_recognized")
            misty.StopKeyPhraseRecognition()
            look_side_to_side()
            time.sleep(6.5)

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

def start_listening():
    global first_contact
    first_contact = True
    misty.RegisterEvent("voice_cap", Events.VoiceRecord, callback_function = voice_rec_callback, debounce = 10, keep_alive = False)
    misty.RegisterEvent("key_phrase_recognized", Events.KeyPhraseRecognized, callback_function = key_phrase_callback, debounce = 10, keep_alive = False)
    misty.StartKeyPhraseRecognition()
    print("Misty is listening to 'Hey Misty!'")

def keep_listening():
    global first_contact
    first_contact = False
    misty.RegisterEvent("voice_cap", Events.VoiceRecord, callback_function = voice_rec_callback, debounce = 10, keep_alive = False)
    misty.CaptureSpeech(silenceTimeout = 10000, requireKeyPhrase = False)
    print("Misty is listening to speech ('Hey Misty!' is not required)")

def set_head_yaw_callback(data):
    global head_yaw
    head_yaw = data["message"]["value"]
    #print(f"head_yaw set to: {head_yaw}")

def set_head_pitch_callback(data):
    global head_pitch
    head_pitch = data["message"]["value"]
    #print(f"head_pitch set to: {head_pitch}")

def key_phrase_callback(data):
    print(f"Misty heard you, trying to wake her up. Confidence: {data['message']['confidence']}%")
    #misty.Speak("Hello")

def respond():
    # TODO: feldolgozni a beérkezett beszédet, választ küldeni
    misty.Speak("OK")
    print("misty responded")

def voice_rec_callback(data):
    global responded
    print("voice_rec_callback elindult")
    if data["message"]["success"]:
        if first_contact is True:
            encoded_string = misty.GetAudioFile("capture_HeyMisty.wav", True).json()["result"]["base64"]
        else:
            encoded_string = misty.GetAudioFile("capture_Dialogue.wav", True).json()["result"]["base64"]
        misty.DeleteAudio("capture_HeyMisty.wav")
        misty.DeleteAudio("capture_Dialogue.wav")
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
        responded = True
    else:
        print("Unsuccessful voice recording")
        responded = True
    print("unregistering...")
    if "voice_cap" in misty.active_event_registrations:
        misty.UnregisterEvent("voice_cap")
    if "key_phrase_recognized" in misty.active_event_registrations:
        misty.UnregisterEvent("key_phrase_recognized")
    print("unregistering finished")
    misty.StopKeyPhraseRecognition()

def face_rec_callback(data):
    global searching_for_face, misty, responded
    print("face found!")
    #print(data["message"]["label"])

    if searching_for_face:
        searching_for_face = False
        #misty.ChangeLED(0, 255, 0);
        misty.DisplayImage("e_Love.jpg")
        start_listening()

    if responded and not searching_for_face:
        responded = False
        start_listening()
        #keep_listening()

    bearing = data["message"]["bearing"]
    elevation = data["message"]["elevation"]
    #print(f"bearing: {bearing}")
    #print(f"elevation: {elevation}")

    local_head_yaw = head_yaw
    local_head_pitch = head_pitch
    local_yaw_right = yaw_right
    local_yaw_left = yaw_left
    local_pitch_up = pitch_up
    local_pitch_down = pitch_down

    if bearing != 0 and elevation != 0:
        misty.MoveHead(local_head_pitch + ((local_pitch_down - local_pitch_up) / 33) * elevation, 0, local_head_yaw + ((local_yaw_left - local_yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    elif bearing != 0:
        misty.MoveHead(None, 0, local_head_yaw + ((local_yaw_left - local_yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    else:
        misty.MoveHead(local_head_pitch + ((local_pitch_down - local_pitch_up) / 33) * elevation, 0, None, None, 5 / abs(elevation))

def look_side_to_side():
    print("looking for face...")
    global misty, responded
    misty.DisplayImage("e_DefaultContent.jpg")
    misty.StopKeyPhraseRecognition()
    misty.ChangeLED(255, 255, 255)
    responded = False

    if head_yaw > 0:
        misty.MoveHead(get_random_int(-20, 0), 0, -40, None, 4)
    else:
        misty.MoveHead(get_random_int(-20, 0), 0, 40, None, 4)

def get_random_int(min, max):
    return random.randint(min, max)

def stop_skill():
    global skill_running
    skill_running = False
    misty.UnregisterAllEvents()
    misty.StopRecordingAudio()
    misty.StopFaceRecognition()
    misty.StopKeyPhraseRecognition()
    misty.ChangeLED(255, 255, 255)
    misty.MoveHead(-15.0, 0.0, 0.0, None, 1)
    misty.DisplayImage("e_DefaultContent.jpg")



if __name__ == "__main__":
    try:
        ip_address = "10.2.8.5"
        misty = Robot(ip_address)
        print(ip_address)
        #misty.Speak("Hello")
        start_face_following_skill()

    except Exception as ex:
        print(ex)

    finally:
        misty.StopFaceRecognition()
        misty.UnregisterAllEvents()
        misty.ChangeLED(255, 255, 255)
        misty.DisplayImage("e_DefaultContent.jpg")
        misty.StopKeyPhraseRecognition()
        print("face rec stopped, unregstered all events")
