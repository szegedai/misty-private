from mistyPy.Robot import Robot
from mistyPy.Events import Events
from datetime import datetime, timezone

looked_at = None
head_yaw = None
robot_yaw = None
_1b = None
_2b = None
in_progress = None
misty = None

def start():
    global looked_at, head_yaw, robot_yaw, _1b, _2b, in_progress, misty
    misty.ChangeLED(0, 0, 255)
    looked_at = datetime.now(timezone.utc)
    misty.MoveHead(-15.0, 0.0, 0.0, None, 1)
    misty.StartRecordingAudio("deleteThis.wav")
    misty.PauseSkill(4000)
    misty.ChangeLED(0, 255, 0)
    #if (_params.turn_off_hazards) misty.UpdateHazardSettings(false, false, false, null, null, false, 0)

    #Setting some global variables as normal var <variable_name> cannot be accessed in event callbacks
    head_yaw = 0.0
    robot_yaw = 0.0

    #Used for smoothening data - barely helps :D - Gotta do more layers for better softening
    _1b = 0.0
    _2b = 0.0

    in_progress = False

    registerAudioLocalisation()
    registerIMU()
    registerActuatorPosition()

    misty.KeepAlive()

def registerIMU():
    global misty
    misty.RegisterEvent("heading", Events.IMU, callback_function = heading_callback, debounce = 100, keep_alive = True)

def registerActuatorPosition():
    global misty
    misty.RegisterEvent("positions", Events.ActuatorPosition, condition = [EventFilters.ActuatorPosition.HeadYaw], callback_function = positions_callback, debounce = 100 , keep_alive = True)

def registerAudioLocalisation():
    global misty
    #misty.AddReturnProperty("sound", "DegreeOfArrivalSpeech")
    misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function = sound_callback, debounce = 100, keep_alive = True)

def positions_callback(data):
    global head_yaw
    head_yaw_local = data["message"]["value"]
    head_yaw_local = -45.0 if head_yaw_local < -45.0 else head_yaw_local
    head_yaw_local = 45.0 if head_yaw_local > 45.0 else head_yaw_local
    head_yaw = head_yaw_local

def heading_callback(data):
    global robot_yaw
    yaw = data["message"]["yaw"]
    if yaw > 180: yaw -= 360
    robot_yaw = yaw

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

    global in_progress, looked_at, misty
    in_progress = True

    #head motion
    raw_final_head_pose = head_yaw + heading
    actuate_to = raw_final_head_pose
    actuate_to = -45.0 if actuate_to <- 45.0 else actuate_to
    actuate_to = 45.0 if actuate_to > 45 else actuate_to
    print(f"{actuate_to} <- Head to move to")
    misty.MoveHead(-15.0, 0.5, actuate_to, None, 1)

    #body motion
    if abs(raw_final_head_pose >= 45):
        misty.PauseSkill(1000)
        global_heading = offset_heading(heading + (head_yaw_at_start * 2.0))
        if global_heading > 180: global_heading-=360
        misty.Drive(0, 30) if angle_difference(robot_yaw_at_start, global_heading) >= 0 else misty.Drive(0, -30)
        print(f"{global_heading} <- Body to move to")
        initial_error = abs(angle_difference(robot_yaw_at_start, global_heading))
        current_abs_error = initial_error
        head_reset_done = False
        while (abs(robot_yaw - global_heading) >= 10):
            current_abs_error = abs(angle_difference(robot_yaw, global_heading))
            if current_abs_error / initial_error < 0.45 and not head_reset_done:
                head_reset_done = True
                misty.MoveHead(-15.0, 0.0, 0.0, None, 2.5)
            misty.PauseSkill(10)
        misty.Stop()
    else:
        misty.PauseSkill(3000)
    print("DONE")
    looked_at = datetime.now(timezone.utc)
    in_progress = False

def sound_callback(data):
    global in_progress, _1b, _2b, misty
    vector = 0.4 * to_robot_frame(data['message']['degreeOfArrivalSpeech']) + 0.35 * _1b + 0.25 * _2b
    if seconds_past(looked_at) > 5.0 and not in_progress:
        misty.UnregisterEvent("sound")
        in_progress = True
        print(f"{vector} <-- Look At Input Global")
        look_at(vector, robot_yaw, head_yaw)
        registerAudioLocalisation()
    _2b = _1b
    _1b = vector


if __name__ == "__main__":
    try:
        ip_address = "10.2.8.5"
        misty = Robot(ip_address)
        print(ip_address)
        #misty.Speak("Hello")
        start()

    except Exception as ex:
        print(ex)

    finally:
        misty.UnregisterAllEvents()
