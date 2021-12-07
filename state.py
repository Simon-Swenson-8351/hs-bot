import abc
import random
import pyautogui
import datetime
import numpy
import time
import PIL.ImageGrab
import threading

import data
import mouse



class Transition(object):

    def __init__(self, end_state = None):
        self.end_state = end_state

    def condition_met(self):
        pass

    def start(self, last_state, transition_taken):
        pass



class TransitionAlways(Transition):

    def __init__(self, end_state = None):
        super().__init__(end_state)

    def condition_met(self):
        return True



class TransitionTemplateFound(Transition):

    MODE_AND = 0
    MODE_OR = 1

    def __init__(self, template_list: list[data.Template], game_frame, end_state = None, mode = MODE_OR):
        super().__init__(end_state)
        self.template_list = template_list
        self.game_frame = game_frame
        self.mode = mode

    def condition_met(self):
        if self.mode == self.MODE_AND:
            return self.condition_met_and()
        elif self.mode == self.MODE_OR:
            return self.condition_met_or()
        raise Exception("unknown mode " + str(self.mode))

    def condition_met_and(self):
        for template in self.template_list:
            if not template.threshold_reached(self.game_frame.screenshot):
                return False
        return True

    def condition_met_or(self):
        for template in self.template_list:
            if template.threshold_reached(self.game_frame.screenshot):
                return True
        return False



class TransitionTimer(Transition):

    def __init__(self, state_to_listen_to, dur_low: float, dur_high: float, end_state = None):
        super().__init__(end_state)
        self.state_to_listen_to = state_to_listen_to
        self.dur_low = dur_low
        self.dur_high = dur_high
        self.duration = None

    def condition_met(self):
        return (datetime.datetime.now() - self.state_to_listen_to.timestamp).total_seconds() > self.duration

    def start(self, last_state, transition_taken):
        self.duration = random.uniform(self.dur_low, self.dur_high)



class State(object):

    def __init__(self, name: str, transitions: list[Transition] = None):
        self.name = name
        self.timestamp = None
        if transitions is None:
            self.transitions = []
        else:
            self.transitions = transitions

    def start(self, last_state, transition_taken):
        self.timestamp = datetime.datetime.now()
        for transition in self.transitions:
            transition.start(last_state, transition_taken)

    def advance(self):
        t = State.check_transitions(self.transitions)
        if t is not None:
            t.end_state.start(self, t)
            return t.end_state
        return self

    @classmethod
    def check_transitions(cls, transitions):
        for transition in transitions:
            if transition.condition_met():
                return transition
        return None



class StateClick(State):

    def __init__(
            self,
            name: str,
            mouse_lock: threading.Lock,
            bounding_box, 
            num_clicks: int = 1,
            timeout: float = -1,
            transitions_during: list[Transition] = None,
            transitions_after: list[Transition] = None):

        super().__init__(name, transitions_after)
        # to disambiguate things
        self.transitions_after = self.transitions
        self.mouse_lock = mouse_lock
        self.bounding_box = bounding_box
        self.total_clicks = num_clicks
        self.cur_clicks = 0
        if timeout > 0:
            self.transitions_after.append(TransitionTimer(
                self,
                timeout,
                timeout + timeout * 0.1,
                self))
        if transitions_during is None:
            self.transitions_during = []
        else:
            self.transitions_during = transitions_during
        self.target_x = None
        self.target_y = None
        self.last_state = None
        self.transition_taken = None
        self.started = False

    # Necessary in case another state is holding the mouse lock
    def try_start(self):
        if self.mouse_lock.acquire(blocking=False):
            last_state = self.last_state
            transition_taken = self.transition_taken
            super().start(last_state, transition_taken)
            src_x, src_y = pyautogui.position()
            if last_state is self and \
                    src_x == self.target_x and \
                    src_y == self.target_y:
                # same state and the cursor hasn't moved - don't resample the 
                # target
                pass
            else:
                bb = self.bounding_box
                self.target_x = int(random.uniform(bb.coords[0], bb.coords[2]))
                self.target_y = int(random.uniform(bb.coords[1], bb.coords[3]))
            bc = mouse.bezier_builder(
                numpy.array([src_x, src_y], dtype=numpy.float32),
                numpy.array([self.target_x, self.target_y], dtype=numpy.float32)
            )
            self.mouse_mover = mouse.MouseMover(bc)
            self.cur_clicks = 0
            self.started = True

    #override
    def start(self, last_state, transition_taken):
        self.started = False
        self.last_state = last_state
        self.transition_taken = transition_taken
        self.try_start()

    #override
    def advance(self):
        if not self.started:
            self.try_start()
            if not self.started:
                return self
        t = State.check_transitions(self.transitions_during)
        if t != None:
            self.mouse_lock.release()
            t.end_state.start(self, t)
            return t.end_state
        # find out if we're currently moving or clicking
        if not self.mouse_mover.done():
            self.mouse_mover.continue_move()
        else:
            # clicking
            if self.total_clicks < 1 or self.cur_clicks < self.total_clicks:
                pyautogui.click()
                self.cur_clicks += 1
            t = State.check_transitions(self.transitions_after)
            if t != None:
                self.mouse_lock.release()
                t.end_state.start(self, t)
                return t.end_state
        return self

# Insert's a delay after this transition, effectively creating a new state
# Note: There will only be one transition to and from the new state 
# created in the middle of this transition. If you need more transitions
# from that new wait state, you need to add them manually.
# returns the newly created state, with its only transition the new 
# delay to the given transition's old end_state
# Use case: delay after a template is found
def insert_delay(name: str, start_state: State, transition: Transition, wait_low: float, wait_high: float):
    r = State(name)
    wait_t = TransitionTimer(r, wait_low, wait_high, transition.end_state)
    transition.end_state = r
    r.transitions.append(wait_t)
    return r

def connect_with_delay(start_state: State, end_state: State, wait_low: float, wait_high: float):
    t = TransitionTimer(start_state, wait_low, wait_high, end_state)
    start_state.transitions.append(t)
    return t