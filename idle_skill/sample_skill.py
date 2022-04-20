# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter, so we can use its functions (we call this function from the idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation

from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters
import tts

sample_skill_running = None
robot = None

def captouch_callback(data):
    global sample_skill_running
    print("captouch")
    sample_skill_running = False

def bump_callback(data):
    global robot
    robot.ChangeLED(255, 0, 0)


def start_sample_skill(misty):
    global sample_skill_running
    global robot
    robot = misty

    tts.synthesize_text_to_robot(misty, "Elindult a minta szkill.", "response.wav")
    print(f"{sample_skill_running}")
    print("sample skill started")
    sample_skill_running = True
    if misty is not None:

        misty.ChangeLED(0,255,0)
        misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function = captouch_callback, debounce = 2000, keep_alive = True)
        misty.RegisterEvent("bump_sensor_pressed", Events.BumpSensor, callback_function = bump_callback, debounce = 10, keep_alive = True)
        while sample_skill_running:
            print("sample skill is running")

        misty.UnregisterAllEvents()

    return True
