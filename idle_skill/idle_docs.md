# Misty idle skill and skill switching



## main function

In the main function we first initialize the robot, so we can send commands to it.

After initializing the robot, we start an infinite **while** loop. This loop is to keep the program alive and make skill switching possible. There's probably a better solution for this, but this is how it works for now.

## Skill switching

We have a **skill_finished** global variable and its value is True when we start the program. In the loop, we keep checking its value and if it's True, we call the **start_idle_skill()** function. This function will start the idle skill, and set the **skill_finished** variable to False.

### Starting an external skill from the idle skill

When we want to start an external skill from the idle skill, we first call the **stop_idle_skill()** function. This function unregisters all events, stop any services used in the skill and stops misty's movement. Then we can call an external skill, and we should set the skill_finished variable's value as the skills return value (e.g skill_finished = sample_skill.start_sample_skill(misty)).

### External skills

**Requirements:**

- external skills should be functions with an infinite loop (so we don't exit the skill immediately)
- they get the robot as a parameter, so we can send commands to it from the skill
- they need a way to exit the loop, so we can return to the idle skill
- they need to stop all events, services, movements etc. they're using after exiting the loop
- then they need to return **True**, so the while loop in the main program starts the idle skill again

sample_skill.py can be used as an example/starting point