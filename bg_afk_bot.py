import PIL.ImageGrab
import time
import threading

import data
import state
import game_region
import config

class StateManager(object):

    def __init__(self, game_region: game_region.GameRegion):
        self.game_region = game_region
        self.screenshot = None

        # setup the state transition graph
        state_menu_bg = state.StateClick(
            "menu_bg",
            data.mouse_lock,
            game_region.bounding_boxes["play-bg"],
            timeout = 5
        )
        state_in_queue = state.State("in_queue")
        state_cancel_queue =  state.StateClick(
            "cancel_queue",
            data.mouse_lock,
            game_region.bounding_boxes["cancel-queue"],
            timeout = 5
        )

        # when the button to cancel queue goes away
        state_queue_end = state.State("queue_end")
        # when the "choose a hero" screen comes up
        state_game_started = state.State("game_started")
        # immediately after state_game_started. This is necessary because 
        # state_game_started has a side-effect that resets the game timer,
        # and we don't want to trigger that every time we click refresh
        state_in_game = state.State("in_game")
        state_click_options = state.StateClick(
            "click_options",
            data.mouse_lock,
            game_region.bounding_boxes["options"],
            timeout = 5
        )
        state_click_concede = state.StateClick(
            "click_concede",
            data.mouse_lock,
            game_region.bounding_boxes["concede"],
            timeout = 5
        )
        state_find_refresh = state.State("find_refresh")
        state_find_refresh_after = state.State("find_refresh_after")
        state_click_refresh = state.StateClick(
            "click_refresh",
            data.mouse_lock,
            game_region.bounding_boxes["bg-refresh"]
        )
        state_click_to_end_game = state.StateClick(
            "click_to_end_game",
            data.mouse_lock,
            game_region.bounding_boxes["menu-dead-zone"],
            timeout = 2
        )
        state_menu_wait = state.State("menu_wait")
        state_click_ok_opponent_failed_to_connect = state.StateClick(
            "click_ok_opponent_failed_to_connect",
            data.mouse_lock,
            game_region.bounding_boxes["opponent-failed-to-connect-ok"]
        )
        # After opponent failed to connect or we get disconnected, we may end up 
        # on the bg menu or the main menu
        state_menu_unk = state.State("state_menu_unk")
        # need a different state because from before, because now we need to click
        # through all the menus to get back to the BG landing screen
        state_click_reconnect_main_menu = state.StateClick(
            "click_reconnect_main_menu",
            data.mouse_lock,
            game_region.bounding_boxes["reconnect"]
        )
        state_click_modes = state.StateClick(
            "click_modes",
            data.mouse_lock,
            game_region.bounding_boxes["menu-main-modes"],
            timeout = 5
        )
        # If we got new quests or something, they may appear after clicking
        # "opponent failed to connect ok"
        # so let's default to clicking the dead zone if no other templates 
        # were found on the main menu
        state_click_main_menu_dead_zone = state.StateClick(
            "click_main_menu_dead_zone",
            data.mouse_lock,
            game_region.bounding_boxes["menu-dead-zone"]
        )
        state_click_mode_bg = state.StateClick(
            "click_mode_bg",
            data.mouse_lock,
            game_region.bounding_boxes["menu-modes-bg"],
            timeout = 5
        )
        state_click_mode_choose = state.StateClick(
            "click_mode_choose",
            data.mouse_lock,
            game_region.bounding_boxes["menu-modes-choose"],
            timeout = 5
        )


        transition_to_in_queue = state.TransitionTemplateFound(
            [game_region.templates["in-queue"], game_region.templates["in-queue-glowing"]],
            self,
            state_in_queue)
        state_menu_bg.transitions.append(transition_to_in_queue)



        transition_to_queue_end = state.TransitionTemplateFound(
            [game_region.templates["queue-end"]],
            self,
            state_queue_end
        )
        state_in_queue.transitions.append(transition_to_queue_end)
        transition_to_click_ok_opponent_failed_to_connect = state.TransitionTemplateFound(
            [game_region.templates["opponent-failed-to-connect"]],
            self,
            state_click_ok_opponent_failed_to_connect
        )
        state.connect_with_delay(state_queue_end, state_menu_unk, 180, 240)
        state.connect_with_delay(state_in_queue, state_cancel_queue, 300, 330)
        transition_to_click_reconnect_main_menu = state.TransitionTemplateFound(
            [game_region.templates["disconnected"]],
            self,
            state_click_reconnect_main_menu
        )
        state_menu_unk.transitions.append(transition_to_click_reconnect_main_menu)
        state_cancel_queue.transitions.append(transition_to_click_reconnect_main_menu)
        # false positive
        state.connect_with_delay(state_cancel_queue, state_menu_bg, 20, 30)

        transition_to_game_started = state.TransitionTemplateFound(
            [game_region.templates["game-start-bg"]],
            self,
            state_game_started
        )
        state_queue_end.transitions.append(transition_to_game_started)

        transition_to_in_game = state.TransitionAlways(state_in_game)
        state_game_started.transitions.append(transition_to_in_game)

        transition_to_click_options = state.TransitionTimer(
            state_game_started,
            2016, # number of seconds in 33.6 minutes
            2026,
            state_click_options
        )
        state_in_game.transitions.append(transition_to_click_options)

        transition_to_click_concede = state.TransitionTemplateFound(
            [game_region.templates["concede"]],
            self,
            state_click_concede
        )
        state_click_options.transitions.append(transition_to_click_concede)

        transition_to_click_to_end_game = state.TransitionTemplateFound(
            [game_region.templates["game-over-bg"]],
            self,
            state_click_to_end_game
        )
        state_in_game.transitions.append(transition_to_click_to_end_game)
        state_click_concede.transitions_during.append(transition_to_click_to_end_game)
        state_click_options.transitions_during.append(transition_to_click_to_end_game)
        state_find_refresh.transitions.append(transition_to_click_to_end_game)
        state_find_refresh_after.transitions.append(transition_to_click_to_end_game)
        state_click_refresh.transitions_during.append(transition_to_click_to_end_game)

        state.connect_with_delay(state_in_game, state_find_refresh, 300, 360)

        transition_to_find_refresh_after = state.TransitionTemplateFound(
            [game_region.templates["bg-refresh-1"], game_region.templates["bg-refresh-2"]],
            self,
            state_find_refresh_after,
            state.TransitionTemplateFound.MODE_AND
        )
        state_find_refresh.transitions.append(transition_to_find_refresh_after)

        state.connect_with_delay(state_find_refresh_after, state_click_refresh, 0, 5)


        state_click_refresh.transitions.append(transition_to_in_game)


        transition_to_menu_wait = state.TransitionTemplateFound(
            [game_region.templates["play-bg"]],
            self,
            state_menu_wait
        )
        state_click_to_end_game.transitions.append(transition_to_menu_wait)

        state.connect_with_delay(state_menu_wait, state_menu_bg, 2, 3)

        state.connect_with_delay(state_click_ok_opponent_failed_to_connect, state_menu_unk, 20, 30)
        state_menu_unk.transitions.append(transition_to_click_ok_opponent_failed_to_connect)


        state.connect_with_delay(
            state_click_reconnect_main_menu,
            state_menu_unk,
            20,
            30
        )

        transition_to_click_modes = state.TransitionTemplateFound(
            [game_region.templates["menu-main-modes"]],
            self,
            state_click_modes
        )
        state_menu_unk.transitions.append(transition_to_click_modes)

        transition_to_click_mode_choose = state.TransitionTemplateFound(
            [game_region.templates["menu-modes-bg"]],
            self,
            state_click_mode_choose
        )
        state_click_modes.transitions.append(transition_to_click_mode_choose)

        transition_to_click_mode_bg = state.TransitionTemplateFound(
            [game_region.templates["menu-modes-header"]],
            self,
            state_click_mode_bg
        )
        state_click_modes.transitions.append(transition_to_click_mode_bg)

        state_click_mode_bg.transitions.append(transition_to_click_mode_choose)

        state_click_mode_choose.transitions.append(transition_to_menu_wait)

        state.connect_with_delay(
            state_menu_unk,
            state_click_main_menu_dead_zone,
            2,
            4
        )
        state.connect_with_delay(
            state_click_main_menu_dead_zone,
            state_menu_unk,
            20,
            30
        )

        # Since we don't know whether we're in the main menu or the bg menu, 
        # just append a template transition for the bg menu.
        state_menu_unk.transitions.append(transition_to_menu_wait)

        state_cancel_queue.transitions_during.append(transition_to_queue_end)

        self.cur_state = state_menu_bg
        self.cur_state.start(None, None)

    def advance(self, screenshot):
        self.screenshot = self.game_region.crop_screenshot(screenshot)
        self.cur_state = self.cur_state.advance()


        

def create_bounding_box_infos():
    tmp_list = []
    tmp_list.append(data.BoundingBoxInfo("play-bg",                       [630, 359, 677, 402]))
    tmp_list.append(data.BoundingBoxInfo("menu-dead-zone",                [747,  29, 843, 429]))
    tmp_list.append(data.BoundingBoxInfo("concede",                       [388, 163, 465, 178]))
    tmp_list.append(data.BoundingBoxInfo("options",                       [825, 463, 843, 475]))
    tmp_list.append(data.BoundingBoxInfo("bg-refresh",                    [485,  72, 518, 110]))
    tmp_list.append(data.BoundingBoxInfo("cancel-queue",                  [415, 396, 458, 419]))
    tmp_list.append(data.BoundingBoxInfo("reconnect",                     [311, 352, 399, 377]))
    tmp_list.append(data.BoundingBoxInfo("opponent-failed-to-connect-ok", [404, 277, 447, 295]))
    tmp_list.append(data.BoundingBoxInfo("menu-main-modes",               [377, 244, 475, 257]))
    tmp_list.append(data.BoundingBoxInfo("menu-modes-bg",                 [385, 130, 453, 195]))
    tmp_list.append(data.BoundingBoxInfo("menu-modes-choose",             [580, 303, 639, 365]))
    result = {}
    for i in tmp_list:
        result[i.name] = i
    return result

def create_template_infos(resolution):
    tmp_list = []
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("disconnected",               resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("in-queue",                   resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("in-queue-glowing",           resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("game-over-bg",               resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("play-bg",                    resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("bg-refresh-1",               resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("bg-refresh-2",               resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("queue-end",                  resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("concede",                    resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("game-start-bg",              resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("opponent-failed-to-connect", resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("menu-main-modes",            resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("menu-modes-header",          resolution, 0.8))
    tmp_list.append(data.TemplateInfo.create_and_fetch_positional_image("menu-modes-bg",              resolution, 0.8))
    
    result = {}
    for i in tmp_list:
        result[i.name] = i
    return result

def should_advance(i, sm_list: list[StateManager]):
    # Do not advance if we are in the menu, and another state manager is 
    # in queue. We don't want multiple bots with the same name to get into
    # the same game and tip off another player.
    sm = sm_list[i]
    if sm.cur_state.name == "menu_bg":
        for j in range(len(sm_list)):
            if j == i:
                continue
            if sm_list[j].cur_state.name == "in_queue":
                return False
    return True

def main():
    time.sleep(5)

    bounding_box_infos = create_bounding_box_infos()
    template_infos = create_template_infos(config.template_resolution)
    state_manager_list = []
    for game_window in config.game_windows:
        gr = game_region.GameRegion(
            game_window["offset"],
            game_window["size"],
            config.template_resolution,
            template_infos,
            config.bounding_box_resolution,
            bounding_box_infos
        )
        state_manager_list.append(StateManager(gr))

    j = 1
    while True:
        screenshot = PIL.ImageGrab.grab()
        for i in range(len(state_manager_list)):
            if i >= j:
                # this ith bot hasn't been spun up yet - need to wait 
                # for each previous bot to have completed the queue first 
                # to ensure we get into different games
                continue
            if config.debug:
                print("State manager " + str(i) + ": " + state_manager_list[i].cur_state.name)
            if should_advance(i, state_manager_list):
                state_manager_list[i].advance(screenshot)
        if j < len(state_manager_list) and \
                state_manager_list[j - 1].cur_state.name == "queue_end":
            # if we still haven't spun up all the bots and
            # the latest bot spun up is through the queue,
            # increment j to spin up the next bot
            j += 1

    

if __name__ == "__main__":
    main()