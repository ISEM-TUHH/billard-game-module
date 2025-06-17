from .GameImage import GameImage
import numpy as np
from flask import Flask, jsonify, render_template, request, redirect, session
from .Elo import Elo

def get_site_game_local(self):
    self.supermode = "game-local"
    self.submode = "base"
    self.game_local_round = None

    self.beamer_make_gameimage()
    return render_template("game_local.html")

def game_local_start_round(self):
    res = request.json
    
    self.current_player = 0 # index of player, either 0 or 1 -> eventuelly will get set by chance or whatever
    self.player = [{
        "name": res["p1"],
        "team": res["t1"]
    },{
        "name": res["p2"],
        "team": res["t2"]
    }]

    # reset logic
    self.game_last_remaining_balls = {"full": 7, "half": 7, "eight": 1}
    self.game_ball_groups = [] # after they are determined: 1st: player 1 group etc

    self.submode = "break"
    self.beamer_make_gameimage()
    return "Starting game"

def game_local_enter_round(self):
    """ This method implements the entire billard game logic for a round
    """

    # forward_coords and beamer_correct_coords both save the coords when they are called in this supermode
    coords = self.game_coords
    remaining = self.get_remaining_balls(coords)
    print(remaining)
    # determining the group of the current player in an open field (in the beginning)
    if self.game_ball_groups == []: # this determines an open field/game
        if (remaining["half"] < 7 or remaining["full"] < 7) and remaining["eight"] != 0 and (remaining["half"] - remaining["full"] != 0):
            self.game_ball_groups = [0,0]
            self.game_ball_groups[self.current_player] = "full" if (remaining["half"] - remaining["full"]) > 0 else "half"
            self.game_ball_groups[self.current_player - 1] = "half" if (remaining["half"] - remaining["full"]) > 0 else "full" # this works as python allows -1 as index for the last item
        else:
            self.change_player() # if there was no decision made
        print(f"Current groups: {self.game_ball_groups}")
        self.game_last_remaining_balls = remaining
        
    else: # if the game is closed
        group = self.game_ball_groups[self.current_player]
        if self.game_last_remaining_balls[group] > remaining[group]: # if the there where balls from current players group sunk
            print(f"This player has sunk a ball during their turn - they may play again")
            print(self.game_last_remaining_balls[group], remaining[group])
            self.game_last_remaining_balls = remaining
            # the player can play again 
            if remaining[group] == 0 and group != "eight": # if there are no balls left of the group, switch group to eight
                self.game_ball_groups[self.current_player] = "eight"
            elif group == "eight" and remaining[group] == 0:
                # this player has sunk the eight while they were supposed to -> win!!!
                print(f"{self.get_current_player_name()} has won the game!")
                self.handle_win()

        else: 
            self.change_player()

    group = self.game_ball_groups[self.current_player]
    filtered = self.filterData(group, coords)
    self.beamer_make_gameimage(coords = filtered)
    print(f"Current groups: {self.game_ball_groups}, remaining this round: {remaining} (last round: {self.game_last_remaining_balls})")
    return jsonify({
        "current-player": self.get_current_player_name(),
        "remaining-balls": remaining,
        "groups": self.game_ball_groups
        })


def get_current_player_name(self, theother=False):
    if theother:
        return self.player[self.current_player-1]["name"]
    return self.player[self.current_player]["name"]

def get_display_string(self):
    """ Compiles a nice string to be displayed on the beamer
    """
    cp = self.current_player
    name1 = self.player[0]["name"] if cp == 1 else self.player[0]["name"].upper()
    name2 = self.player[1]["name"] if cp == 0 else self.player[1]["name"].upper()
    g = self.game_ball_groups
    r = self.game_last_remaining_balls
    if g == []: # open field
        return f"{name1} : (open) : {name2}"
    return f"{name1} ({g[0]}) {r[g[0]]}:{r[g[1]]} {name2} ({g[1]})"

# --------------- Internal -------------------
def handle_win(self):
    """ This handles the win of a player, updating their elo etc. NOT IMPLEMENTED YET!
    """
    name = self.get_current_player_name()
    print(f"Congrats to {name}!")
    m = Elo()
    return 0
    

def change_player(self):
    self.current_player = (self.current_player + 1) % 2 # will always switch between 0 and 1
    print(f"Changed player to {self.get_current_player_name()}")

def filterData(self, group, data):
    """ Filter only the balls of the current player's group to be displayed/shots to be calculated

    :param group: the group of the balls to highlight ("full", "half", "eight")
    :type group: str
    :param data: coords from the camera
    :type data: dict
    """
    names = []
    match group:
        case "full":
            names = ["1","2","3","4","5","6","7","white"]
        case "eight":
            names = ["eight","white"]
        case "half":
            names = ["9","10","11","12","13","14","15","white"]

    filteredData = {}
    for d in data:
        if d in names:
            filteredData[d] = data[d]
    
    #print(filteredData, group)
    return filteredData

def get_current_players_ball_coords(self):
    if len(self.game_ball_groups) == 0:
        return self.coords
    group = self.game_ball_groups[self.current_player]
    return self.filterData(group, self.coords)

def get_remaining_balls(self, data):
    """ Filters the data by groups and counts the ball per group (full, half, eight)
    """
    return {
        "half": len(self.filterData("half", data).keys())-1,
        "full": len(self.filterData("full", data).keys())-1,
        "eight": len(self.filterData("eight", data).keys())-1 # -1 due to the white ball being counted too
    }


if __name__ == "__main__":
    data = {"1":{"a":2},"2":{"a":2}, "9":{"a":2}}
    print(filterData(0, "half", data))