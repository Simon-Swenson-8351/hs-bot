import time
import datetime
import numpy
import PIL.ImageGrab
import threading

import state_hero_power_bot
import config

def main():
    time.sleep(5)
    cur_state = state_hero_power_bot.StateClickPlay()

    start_time = datetime.datetime.now()
    while True:
        print(type(cur_state).__name__)
        cur_state = cur_state.advance(numpy.array(PIL.ImageGrab.grab().convert("L")))
        end_time = datetime.datetime.now()
        time_delta = (end_time - start_time).total_seconds()
        if time_delta < config.min_cycle_time:
            time.sleep(config.min_cycle_time - time_delta)
        start_time = end_time



if __name__ == "__main__":
    main()