from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters
import tts

sample_skill_running = None

def captouch_callback(data):
    global sample_skill_running
    print("captouch")
    sample_skill_running = False


def start_sample_skill(misty):
    global sample_skill_running
    #misty.PlayAudio("response.wav")
    tts.synthesize_text_to_robot(misty, "Elindult a minta szkill.", "response.wav")
    print(f"{sample_skill_running}")
    print("sample skill started")
    sample_skill_running = True
    if misty is not None:
        #misty.Speak("Sample skill started.")

        misty.ChangeLED(0,255,0)
        misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function = captouch_callback, debounce = 2000, keep_alive = True)
        while sample_skill_running:
            print("sample skill is running")
            #pass
        misty.UnregisterAllEvents()
    else:
        try:
            while sample_skill_running:
                print("sample skill is running")
        except KeyboardInterrupt:
            pass

    return True
