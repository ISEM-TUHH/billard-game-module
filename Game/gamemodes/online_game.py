from .common_utils import *
from .api_utils import *
from .GameMode import GameMode

class OnlineGame(GameMode):
    """ Play a game of billiards online against another table in the network! 



    Args:
        env (dict): loaded and parsed .env file with configuration and authentication for the global API interface
    """

    def __init__(self, env):
        self.gamemode_name = "Online Game"
        self.state = "init"
        self.score = 0

        self.API = API(env)

        self.TREE = {
            "init": [
                self.request_game,
                {"opened": "wait_reply", "found": "determine_break"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Start an Online Game"
                    },
                    {
                        "type": "central_image",
                        "img": "isem-logo-big"
                    }
                ],
                ["Request Game", {
                    "type": "text",
                    "name": "player",
                    "placeholder": "Player Name"
                }, {
                    "type": "text",
                    "name": "team",
                    "placeholder": "Team"
                }, {
                    "type": "selector",
                    "name": "opponent_table",
                    "options": ""
                }
                ]
            ],
            "wait_reply": [ # 
                self.reply_received,
                {"found": "determine_break", "interrupt": "init"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Waiting for reply..."
                    },
                    {
                        "type": "central_image",
                        "img": "isem-logo-big" # eventually show logo of this and the remote table?
                    }
                ],
                [None, { # just a button that gets clicked when the waiting should be interrupted
                    "type": "button",
                    "name": "interrupt",
                    "placeholder": "Waiting, click to cancel",
                    "value": "Waiting, click to cancel"
                }]

            ],
            "determine_break": [
                self.evaluate_break,
                {"won": "play", "lost": "wait_for_other"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Get as close as possible to win the break!"
                    },
                    {
                        "type": "balls",
                        "coords": self.break_points,
                        "ref": "balls-ref"
                    }
                ],
                ["Evaluate"]
            ],
            "play": [
                self.evaluate_play,
                {"go_on": "play", "change": "wait_for_other", "lost": "finished", "won": "finished"},
                lambda: [
                    {
                        "type": "text",
                        "text": "Play"
                    },

                ]

            ],
            "wait_for_other": [
                self.other_played
            ],
            "build_scene": [
                lambda inp2: self.check_starting_positions(inp2, starting_positions=self.transfered_coords),
                {"True": "play", "False": "build_scene"}
            ],
            "finished": [

            ]
        }


    def request_game(self, inp):
        """ Send a request to the API to open the game or (if selected) look for open games """

    def reply_received(self, inp):
        """ If there was no open game found immediately, just wait. When a game is found or interrupted, the global server will send an (empty) socket event to the client (connected on load of the page), which will call this endpoint to then connect to the global server with authentication to get the update. """

        if "interrupt" in inp.keys():
            # if the button has been clicked, we stop waiting for a response
            return "interrupt", {}, {"message": "Interrupted"}
        # else, a game has been found and we now play the break decision
        # which is a small precision shot between two random places.
        self.break_points = inp["break_points"]
        return "found", {}, {"message": "Game found and started"}

    def evaluate_break(self, inp):
        """ Send the coordinates to the API to determine the smaller distance and who should start. """

        decision = self.API.evaluate_break(inp["coordinates"])

        message = "Won decision, play the break" if decision == "won" else "Lost decision, wait for opponent to break"
        return decision, {}, {"message": message}

    def evaluate_play(self, inp):
        """ Sends the coordinates to the game and handles the decision """

        decision, img_definition = self.API.evaluate_play(inp["coordinates"])

        updates = img_definition # API directly returns a gameimage defining dict
        match decision:
            case "go_on":
                message = "Play again"
            case "change": # if the player cant play again
                message = "Other players turn"
            case "lost":
                message = "You lost!"
            case "won":
                message = "You won!"

        # SHIT

    def other_played(self, inp):
        """ If the other player played and control was transfered (mechanism is the same as OnlineGame.reply_received) """
        self.transfered_coords = {}