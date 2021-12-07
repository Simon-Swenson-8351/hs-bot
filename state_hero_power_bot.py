import state
import data

class ExceptionalConditionGameOver(state.TransitionTemplateFound):

    def __init__(self):
        super().__init__(
            [
                data.templates["game-over-defeat"],
                data.templates["game-over-victory"]
            ],
            lambda: StateClickToEndGame())



class ExceptionalConditionYourTurn(state.TransitionTemplateFound):

    def __init__(self, next_state_factory):
        super().__init__(
            [data.templates["turn-start"]],
            next_state_factory)



class ExceptionalConditionPlayScreen(state.TransitionTemplateFound):

    def __init__(self):
        super().__init__(
            [
                data.templates["play-standard"],
                data.templates["play-wild"]
            ],
            lambda: state.StateWait(2, lambda: StateClickPlay()))



class StateClickPlay(state.StateClick):

    def __init__(self):
        super().__init__(
            data.mouse_lock,
            data.bounding_boxes["play"],
            lambda: StateWaitFirstTurn())



# need a separate state for the first turn, as we need to wait for a 
# certain amount for the "your turn" display to go away before checking 
# it again for the second turn.
class StateWaitFirstTurn(state.StateWait):

    def __init__(self):
        super().__init__(
            -1,
            None,
            [
                ExceptionalConditionGameOver(),
                ExceptionalConditionYourTurn(lambda: state.StateWait(
                    3,
                    lambda: StateWaitTurn(),
                    [ExceptionalConditionGameOver()]))])



class StateClickToEndGame(state.StateClick):

    def __init__(self):
        super().__init__(
            data.mouse_lock,
            data.bounding_boxes["menu-dead-zone"],
            None,
            -1,
            [ExceptionalConditionPlayScreen()])



class StateWaitTurn(state.StateWait):

    def __init__(self):
        super().__init__(
            -1,
            None,
            [
                ExceptionalConditionGameOver(),
                ExceptionalConditionYourTurn(lambda: state.StateWait(
                    3,
                    lambda: StateClickHeroPower(),
                    [ExceptionalConditionGameOver()]))])



class StateClickHeroPower(state.StateClick):

    def __init__(self):
        super().__init__(
            data.mouse_lock,
            data.bounding_boxes["hero-power"],
            lambda: StateWaitTurn(),
            1,
            [ExceptionalConditionGameOver()]
        )