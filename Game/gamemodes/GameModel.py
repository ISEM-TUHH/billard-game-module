from .common_utils import *
#from Elo import Elo

import numpy as np
import random
import secrets
import datetime

class Game:
    """ This is the general game simulation for a typical game of billiards """

    def __init__(self, player1, player2):
        self.player1 = player1 | {"token": secrets.token_hex(32), "group": None, "task": "decide_break", "left": 7}
        self.player2 = player2 | {"token": secrets.token_hex(32), "group": None, "task": "decide_break", "left": 7}

        self.active_player = None
        self.history = {
            "start_time": datetime.datetime.now(),
            "setup": {
                "player1": player1.copy(),
                "player2": player2.copy()
            },
            "break": {},
            "rounds": [],
            "outcome": {}
        }

        self.gid = secrets.token_hex(32) # random 32 byte hexadecimal identifier

    def change_player(self):
        self.inactive_player = self.player1 if self.active_player == self.player1 else self.player2
        self.active_player = self.player1 if self.active_player == self.player2 else self.player2

    def generate_shootout(self):
        """ This generates two ball positions (white and dummy). The player that gets closer to the dummy position starting from the white position wins the break """
        self.break_points = {
            "white": {
                "name": "white",
                "x": random.randrange(200, 600),
                "y": random.randrange(100, 1015),
            },
            "17": { # 17 so it is displayed as a dummy ball (pink)
                "name": "17",
                "x": random.randrange(1500, 2130),
                "y": random.randrange(100, 1015)
            }
        }
        self.history["break"]["points"] = self.break_points

        return {"break_points": self.break_points}

    def evaluate_break(self, coordinates1, coordinates2):
        _, distance1 = metric_distance_closest(coordinates1, self.break_points["17"])
        _, distance2 = metric_distance_closest(coordinates2, self.break_points["17"])
        self.history["break"]["coordinates"] = {
            "player1": coordinates1,
            "player2": coordinates2
        }
        self.history["break"]["distances"] = {
            "player1": distance1,
            "player2": distance2
        }

        # setup the available balls
        self.last_coordinates = {x: 1 for x in ALL_BALLS} # list of all ball names from common_utils, but we need it as a dict

        if distance1 < distance2:
            self.active_player = self.player1
            self.inactive_player = self.player2
        elif distance2 < distance1:
            self.active_player = self.player2
            self.inactive_player = self.player1
        else:
            # randomly choose a winner
            loser = self.player1 if bool(random.randint(0,1)) else self.player2
            self.active_player = loser
            self.change_player() # auto assign the other player  

        self.active_player["task"] = "break"
        self.inactive_player["task"] = "wait"      
        
        return {"winner": self.active_player}

    def evaluate_play(self, auth, coordinates):
        if not auth == self.active_player["token"]:
            return False # false player

        report = coords_report(coordinates, self.last_coordinates)

        player_name = self.active_player["name"]
        other_player_name = self.inactive_player["name"]
        message = player_name # This message tracks the reasoning of the round evaluation
        img_definition = [
            {
                "type": "balls",
                "coords": coordinates
            }
        ]
        action_list = [] # collect keywords, which will get translated into some kind of action later on

        if self.active_player["group"] is None:
            # open game
            message += ": (open game) "
            if report["eight_sunk"]:
                message += "Sunk the eight ball, the other player now breaks"
                # if the eight is sunk in an open game, restart the game with the other player
                self.change_player()
                img_definition = [
                    {
                        "type": "break",
                        "draw_ball": True
                    }
                ]
            elif report["white_sunk"]:
                message += "Sunk the white ball, it is the other players turn"
                self.change_player()
            elif report["n_sunk_legal"] == 0:
                message += "No ball sunk, the other player can now play"
                self.change_player()
            elif report["n_sunk_half"] == report["n_sunk_full"]:
                message += "Exactly the same amount of solid and striped balls sunk, play again"
            elif report["n_sunk_half"] > report["n_sunk_full"]:
                message += f"More striped than solid balls sunk ({report['n_sunk_half']} vs. {report['n_sunk_full']}), assigned group striped, play again"
                self.active_player["group"] = "striped"
                self.inactive_player["group"] = "solid"
            else:
                message += f"More solid than striped balls sunk ({report['n_sunk_full']} vs. {report['n_sunk_half']}), assigned group striped, play again"
                self.active_player["group"] = "solid"
                self.inactive_player["group"] = "striped"

            group = self.active_player["group"]
            self.inactive_player["task"] = "wait" if group is None else f"sink {self.inactive_player['group']}"
            self.active_player["task"] = "play" if group is None else f"sink {group}"
            if group is not None:
                group_key = "half" if group == "striped" else "full"
                wrong_group_key = "half" if group != "striped" else "full"
                self.active_player["left"] = report["left_" + group_key]
                self.inactive_player["left"] = report["left_" + wrong_group_key]


        else:
            # closed game: each player should only sink their color
            message += ": (closed game) "

            group = self.active_player["group"]
            group_key = "half" if group == "striped" else "full"
            wrong_group_key = "half" if group != "striped" else "full"

            self.active_player["left"] = report["left_" + group_key]
            self.inactive_player["left"] = report["left_" + wrong_group_key]

            message += f"[{report['left_full']} solid and {report['left_half']} striped left] "

            if self.active_player["left"] == 0:
                self.active_player["task"] = "sink eight"
                message += "[No more balls of own group left, now sink the eight] "

            if report["eight_sunk"]:
                if self.active_player["task"] is "sink eight":
                    # this player wins
                    message += "Sunk eight and wins the game [END]"
                    pass
                else:
                    message += "Sunk eight when not supposed to, the other player wins [END]"
                    # this player loses
                    self.change_player # in the end, the active player should be the winner
                    pass
            elif report["white_sunk"]:
                message += "White ball sunk, the other player now places the ball in the rectangle and plays"
                self.change_player()
                img_definition = [
                    {
                        "type": "rectangle", # where to put the white ball
                        "c1": {"x": 1500, "y": 10},
                        "c2": {"x": 2100, "y": 1100}
                    }
                ]
            elif report[wrong_group_key] != 0:
                # balls of the wrong group sunk
                message += "Ball of the wrong group sunk, the other player now plays"
                self.change_player()
            elif report["n_sunk_" + group_key] == 0:
                # no ball sunk
                message += "No ball of own group sunk, the other player now plays"
                self.change_player()
            elif report["n_sunk_" + group_key] > 0:
                message += "Only sunk balls of own team, play again"
            

        text1 = f'{self.player1["name"]} {7 - self.player1["left"]}' # example: "Mathis 7"
        text2 = f'{7 - self.player2["left"]} {self.player2["name"]}'
        if self.active_player is self.player1:
            text = f"**{text1}** : {text2}" # example: "**Mathis 7** : 6 Felix" will show as emphasized "Mathis 7" (bold or whatever is currently implemented in GameImage.instructionText) if it is Mathis turn
        else:
            text = f"{text1} : **{text2}**"

        img_definition += [{
            "type": "text", "text": text
        }]
        
        print(message)
        self.history["rounds"].append({
            "timestamp": datetime.datetime.now(),
            "message": message,
            "report": report,
            "coordinates": coordinates
        })
        return message, img_definition, action_list