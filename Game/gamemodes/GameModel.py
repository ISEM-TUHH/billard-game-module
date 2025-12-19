from .common_utils import *
from ..GameEngine import GameEngine
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
            "start_time": str(datetime.datetime.now()),
            "setup": {
                "player1": player1.copy(),
                "player2": player2.copy()
            },
            "break": {},
            "rounds": [],
            "outcome": {}
        }

        self.gid = secrets.token_hex(32) # random 32 byte hexadecimal identifier

        self.engine = GameEngine() # GameEngine object provides methods to get (direct) shot suggestions. They are only shown if the active player wants them to

    def change_player(self):
        """Based on who is the current player (player1 or player2), this switches it. The other player will now be the active player (accessible as self.active_player) and the previously active player will now be inactive (self.inactive_player).
        """
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
            "17": { # 17 so it is displayed as a dummy ball (blue)
                "name": "17",
                "x": random.randrange(1500, 2130),
                "y": random.randrange(100, 1015)
            }
        }
        self.history["break"]["points"] = self.break_points

        return {"break_points": self.break_points}

    def evaluate_break(self, coordinates1, coordinates2):
        """Chooses the player that can break based on two precision shots.
        
        To decide who of the players should play the break, both players play a precision shot between two semi-random points (in self.break_points). The player that is closer to the blue ball wins and can play the break.

        Args:
            coordinates1 (dict): Coordinates of the shot of the first player
            coordinates2 (dict): Coordinates of the shot of the second player

        Returns:
            dict: report with important messages like `{"winner": self.active_player, "distance1": distance of the first player, "distance2": ...}
        """
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
        
        return {"winner": self.active_player, "distance1": distance1, "distance2": distance2}

    def evaluate_play(self, auth, coordinates):
        """Based on common billard rules, control what should happen next.

        This method receives the coordinates after a hit and evaluates wether the player can play again, has made a foul or won/lost the game.

        Args:
            auth (str): 32-byte token, must match the current `self.active_player["token"]`, otherwise this is an illegal request (only the active player should be able to hand in a hit)
            coordinates (dict): Coordinates of the balls of the current position on the billard table.

        Returns:
            str, list, list: message (like a log), a list matching a new GameImage.definition (mostly used for iterating using GameImage.update_definition) and an action list (which is currently not used, could be used for arbtirary outputs in the future) 
        """
        if not auth == self.active_player["token"]:
            return False # false player

        report = coords_report(coordinates, self.last_coordinates)
        self.last_coordinates = coordinates

        player_name = self.active_player["name"]
        other_player_name = self.inactive_player["name"]
        message = player_name # This message tracks the reasoning of the round evaluation
        short_message = ""
        img_definition = [
            {
                "type": "balls",
                "coords": coordinates
            }
        ]
        action_list = [] # collect keywords, which will get translated into some kind of action later on

        if self.active_player["group"] is None:
            # open game: both players can sink balls of both groups, but as soon as they sink more from one than the other group, that group gets assigned to them and the game is "closed". During the break, the black ball can be sunk without loosing the game (a lot of randomnes)
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
                message += f"More solid than striped balls sunk ({report['n_sunk_full']} vs. {report['n_sunk_half']}), assigned group solid, play again"
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

            # debug
            print("GAMEMODEL evaluate play: report: ", report)
            print(" - active player:", self.active_player)
            print(" - group key:", group_key, "wrong group key:", wrong_group_key, "group:", group)

            if self.active_player["left"] == 0:
                self.active_player["task"] = "sink eight"
                message += "[No more balls of own group left, now sink the eight] "

            if report["eight_sunk"]:
                if self.active_player["task"] == "sink eight":
                    # this player wins
                    # define self.message which gets displayed on the table
                    short_message = f"{self.active_player['name']} wins"
                    message += "Sunk eight and wins the game [END]"
                else:
                    short_message = f"{self.inactive_player['name']} wins since {self.active_player['name']} sunk the 8 Ball"
                    message += "Sunk eight when not supposed to, the other player wins [END]"
                    # this player loses
                    self.change_player # in the end, the active player should be the winner
            elif report["white_sunk"]:
                message += "White ball sunk, the other player now places the ball in the rectangle and plays"
                self.change_player()
                img_definition = [
                    {
                        "type": "rectangle", # where to put the white ball
                        "c1": [1500, 10],
                        "c2": [2100, 1100]
                    }
                ]
            elif report["n_sunk_" + wrong_group_key] != 0:
                # balls of the wrong group sunk
                message += "Ball of the wrong group sunk, the other player now plays"
                self.change_player()
            elif report["n_sunk_" + group_key] == 0:
                # no ball sunk
                message += "No ball of own group sunk, the other player now plays"
                self.change_player()
            elif report["n_sunk_" + group_key] > 0:
                message += "Only sunk balls of own team, play again"
            

        text1 = f'{self.player1["name"]} ({self.player1["group"]}) {7 - self.player1["left"]}' # example: "Mathis 7"
        text2 = f'{7 - self.player2["left"]} ({self.player2["group"]}) {self.player2["name"]}'
        if self.active_player is self.player1:
            text = f"**{text1}** : {text2}" # example: "**Mathis 7** : 6 Felix" will show as emphasized "Mathis 7" (bold or whatever is currently implemented in GameImage.instructionText) if it is Mathis turn
        else:
            text = f"{text1} : **{text2}**"

        if self.active_player["tooltips"] and not "[END]" in message: # if the now active player wants to have tooltips, get and show them
            group = self.active_player["group"] if self.active_player["left"] != 0 else "eight"
            shots = self.engine.getShots(coordinates, group=group)
            img_definition.append({"type": "possible_shots", "shots": shots})
            self.history["outcome"] = {
                "winner": self.active_player["name"], # maybe id?
                "elo_exchange": 0 # dummy at the moment. TODO: add ELO system
            }

        img_definition += [{
            "type": "text", "text": text
        },{
            "ref": "balls", "remove": True # do not display the balls
        }]
        
        print("GAME MODEL message:", message)
        self.history["rounds"].append({
            "timestamp": str(datetime.datetime.now()),
            "message": message,
            "report": report,
            "coordinates": coordinates
        })
        self.short_message = short_message
        return message, img_definition, action_list