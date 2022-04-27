# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter, so we can use its functions (we call this function from the idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation

from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters
import time
import tts

sample_skill_running = None
robot = None

def captouch_callback(data):
    global sample_skill_running
    print("captouch")
    sample_skill_running = False


def start_skill(misty):
    global sample_skill_running
    global robot
    robot = misty

    tts.synthesize_text_to_robot(misty, "Elindult a kő papír olló játék", "response.wav")
    print("rps skill started")
    sample_skill_running = True
    if misty is not None:

        misty.ChangeLED(255,255,0)
        misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function = captouch_callback, debounce = 2000, keep_alive = True)
        while sample_skill_running:
            time.sleep(0.1)
            print("rps skill running")

        misty.UnregisterAllEvents()

    return True
