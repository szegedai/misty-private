from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters

sample_skill_running = None

def captouch_callback(data):
    global sample_skill_running
    print("captouch")
    sample_skill_running = False


def start_sample_skill(misty):
    global sample_skill_running
    misty.Speak("Sample skill started.")
    print("sample skill started")
    sample_skill_running = True
    misty.ChangeLED(0,255,0)
    misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function = captouch_callback, debounce = 2000, keep_alive = True)
    while sample_skill_running:
        print("sample skill is running")
        #pass
    misty.UnregisterAllEvents()
    return True
