import numpy as np
import random

from .Elo import Elo

class GameRules:
    """ This class implements rules for 8 ball pool, determining the state of the game based on passed coordinates.

    The decision on who can break is handled by doing a randomized precision shot.

    The state variable (string) determines the image/mode to be projected on the table by the GameImage object
    """
    def __init__(self):
        self.state = "pre" # upon loading the game page
        self.message = "Enter your names and click on start"
        self.groups = ["open", "open"]
        self.current_player = 0
        self.start_precisions = {"player1": "?", "player2": "?"}
        self.last_remaining_balls = {"full": 7, "half": 7, "eight": 1}
        
    def init_start(self, player1, player2): # upon clicking the start game button
        """ Actually starting the game

        This initialises the process to decide who will break.
        :param player1, player2: dict with name, team, elo (from database)
        """
        self.players = [player1, player2]
        
        # initialise the random starting event
        self.display_coords = {
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
        print(self.players)
        self.message = "Get as close as possible to the green ball"
        self.state = "determine"
        

    def determine_start(self, data1):#, data2):
        """ Determine of the players should play the break by having them do a precision shot to a random point on the screen

        :param data1: dict like {"player1": {"name": "ball-5", "x": 123, "y": 456, ...}} with x and y in mm
        """
        if self.state not in ["determine"]:
            return

        distance = int(self.get_distance(self.display_coords["17"], list(data1.values())[0]))
        self.start_precisions[list(data1.keys())[0]] = distance
        print(self.start_precisions)

        if "?" not in self.start_precisions.values():
            # if both players have entered their precisions/distances
            self.current_player = int(self.start_precisions["player1"] > self.start_precisions["player2"])
            print(self.start_precisions["player1"] > self.start_precisions["player2"])

            self.groups = ["open", "open"]
            self.message = f"{self.get_current_player_name()} may break"
            self.state = "break"
        else:
            self.message = f"{self.players[0]['name']}: {self.start_precisions['player1']} mm vs. {self.players[1]['name']}: {self.start_precisions['player2']} mm"
        return distance
        

    def enter_round(self, data):
        """ Register a round and determine the next steps

        :param data: coords dictionary of balls
        :type data: dict
        """
        if self.state not in ["game", "break"]:
            return False

        remaining = self.get_remaining_balls(data)
        self.remaining = remaining

        self.change_flag = False # tracks, if the player has been changed during this round -> prevent it from changing two times
        self.message = "" # reset the message to be displayed
        self.coords = data

        # handle fouls first (this also handles the final sinking of the 8)
        if "eight" not in data.keys(): # if the 8 was sunk...
            if self.groups[self.current_player] != "eight": # ...and it was not supposed to be sunk...
                print("Foul detected: 8 was sunk")
                if self.state == "break": # ...but it was just during break: the other player can break again
                    self.change_player()
                    self.message = f"Foul! {self.get_current_player_name()} may break"
                elif self.state == "game": # ..and it was during the normal game: the other player wins
                    self.change_player()
                    self.handle_win()
            else: # ...and it was supposed to be sunk
                print("Win detected: 8 was sunk")
                self.handle_win()
            return False # this always ends the current round, the state is preserved. Empty is the flag to not display any coordinates/balls
        elif "white" not in data.keys(): # if the white ball was sunk...
            if self.state == "break": # ...but it was during break: the other player can break again
                self.change_player()
                self.message = f"Foul! {self.get_current_player_name()} may break"
            elif self.state == "game": # ...and it was during a normal game round: the other player can place the white ball anywhere and play
                self.change_player()
            # this does not end the round

        # open game:
        if "open" in self.groups:
            if (remaining["half"] < 7 or remaining["full"] < 7) and (remaining["half"] - remaining["full"] != 0): # determine if there was a relevant amount of balls sunk to assign a group
                self.groups[self.current_player] = "full" if (remaining["half"] - remaining["full"]) > 0 else "half"
                self.groups[self.current_player - 1] = "half" if (remaining["half"] - remaining["full"]) > 0 else "full" # this works as python allows -1 as index for the last item
                # do not change the player -> the current player has at least sunk one relevant ball (except for foul, but that was already handled)
            else: # if no group decision could be made
                self.change_player()

        # closed game
        else:
            group = self.groups[self.current_player]
            othergroup = self.groups[self.current_player - 1]
            if self.last_remaining_balls[group] > remaining[group]: # detect, if there was a ball from the player's group sunk
                if remaining[group] == 0: # if all balls of this group where sunk
                    self.groups[self.current_player] = "eight"

            else: # if no ball was sunk
                self.change_player()

            if remaining[othergroup] == 0:
                self.groups[self.current_player - 1] = "eight"

        self.last_remaining_balls = remaining
        self.state = "game"

        self.message = self.get_display_string() if self.message == "" else self.message # if the message has not been set, set it with the default score tracker

        return True


    ########### internal ##############################

    def get_distance(self, coords1, coords2):
        """ Returns the distance (2 norm) between two coordinates (ball coord dicts)
        """
        x1, y1 = int(coords1["x"]), int(coords1["y"])
        x2, y2 = int(coords2["x"]), int(coords2["y"])
        return np.sqrt((x1-x2)**2 + (y1-y2)**2)

    def get_current_player_name(self, theother=False):
        if theother:
            return self.players[self.current_player-1]["name"]
        return self.players[self.current_player]["name"]

    def get_display_string(self):
        """ Compiles a nice string to be displayed on the beamer
        """
        cp = self.current_player
        name1 = self.players[0]["name"] if cp == 1 else self.players[0]["name"].upper()
        name2 = self.players[1]["name"] if cp == 0 else self.players[1]["name"].upper()
        g = self.groups
        r = self.last_remaining_balls
        if "open" in g: # open field
            return f"{name1} : (open) : {name2}"
        return f"{name1} ({g[0]}) {r[g[0]]}:{r[g[1]]} {name2} ({g[1]})"

    def handle_win(self):
        """ This handles the win of a player, updating their elo etc. NOT IMPLEMENTED YET!
        """
        name = self.get_current_player_name()
        print(f"Congrats to {name}!")
        self.message = f"{name} has won the game!"

        self.state = "winner"

        # update elo
        m = Elo()
        self.players = m.match(self.players, self.current_player)
        print(self.players)
        self.state = "finished"
        return

    def change_player(self):
        if self.change_flag: # do not change the player if it has already been changed this round
            return
        self.current_player = (self.current_player + 1) % 2 # will always switch between 0 and 1
        self.change_flag = True
        print(f"Changed player to {self.get_current_player_name()}")

    def filterData(self, group, data, white=True):
        """ Filter only the balls of the current player's group to be displayed/shots to be calculated

        :param group: the group of the balls to highlight ("full", "half", "eight")
        :type group: str
        :param data: coords from the camera
        :type data: dict
        :param white: include the white ball when filtering the balls
        :type white: optional bool
        """
        names = []
        match group:
            case "full":
                names = ["1","2","3","4","5","6","7","white"] # white must always be the last entry
            case "eight":
                names = ["eight","white"]
            case "half":
                names = ["9","10","11","12","13","14","15","white"]

        names = names if white else names[0:-1]

        filteredData = {}
        for d in data:
            if d in names:
                filteredData[d] = data[d]
        
        if group == "open": # if the field is still open
            filteredData = data

        #print(filteredData, group)
        return filteredData

    def get_current_players_ball_coords(self):
        if len(self.groups) == 0:
            return self.coords
        group = self.groups[self.current_player]
        return self.filterData(group, self.coords)

    def get_remaining_balls(self, data):
        """ Filters the data by groups and counts the ball per group (full, half, eight)
        """
        return {
            "half": len(self.filterData("half", data, white=False).keys()),
            "full": len(self.filterData("full", data, white=False).keys()),
            "eight": len(self.filterData("eight", data, white=False).keys())
        }