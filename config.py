bounding_box_resolution = [854, 480]
template_resolution = [854, 480]

game_windows = []
def append_game_window(offsetx, offsety, width, height):
    game_windows.append({
        "offset": [offsetx, offsety],
        "size": [width, height]
    })
# add new lines here for each game region

# for main computer, windows on corners of main screen
append_game_window(1441,  26, 854, 480)    # top-left
append_game_window(1441, 569, 854, 480)    # bottom-left

# for laptop, windows on corners of screen
#append_game_window(   1,  26, 854, 480)    # top-left
#append_game_window(   1, 568, 854, 480)    # bottom-left
#append_game_window(1065,  26, 854, 480)    # top-right
#append_game_window(1065, 568, 854, 480)    # bottom-right

destination_refresh_rate = 60
# go slightly faster than the refresh rate to make sure we don't skip a frame
min_cycle_time = 1 / destination_refresh_rate * 0.9

debug = True