import datetime
import time
import PIL.ImageGrab
import numpy
import pandas
import cProfile

import data
import config



def process_frame(
    template_dict: dict[str, data.Template],
    frame_no: int,
    start_time: datetime.datetime,
    current_list: list[list[float]]
):
    screenshot = numpy.array(PIL.ImageGrab.grab().convert("L"))

    frame_responses = []
    for _, v in template_dict.items():
        frame_responses.append(v.get_response(screenshot))
    current_list.append(frame_responses)

    print("Frame responses: " + ", ".join(map(str, frame_responses)))
    end_time = datetime.datetime.now()
    print("Processing frame " + str(frame_no) + " took:" + str(end_time - start_time))
    return end_time



# just over 5 mins
max_iters = int(round(60 * 60 * 5 * 1.1))

def main():
    templates = data.create_template_infos()
    start_time = datetime.datetime.now()
    filename = start_time.strftime("%Y%m%d_%H%M%S") + "_template_responses.csv"

    current_list = []
    for i in range(max_iters):
        end_time = process_frame(templates, i, start_time, current_list)
        time_delta = (end_time - start_time).total_seconds()
        if time_delta < config.min_cycle_time:
            time.sleep(config.min_cycle_time - time_delta)

        start_time = end_time
    columns_list = []
    for k in templates:
        columns_list.append(k)
    results_array = numpy.array(current_list)
    results_data_frame = pandas.DataFrame(results_array, columns=columns_list)
    results_data_frame.to_csv(filename)


if __name__ == "__main__":
    main()