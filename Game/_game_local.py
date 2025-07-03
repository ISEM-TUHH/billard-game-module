from .GameImage import GameImage
import numpy as np
from flask import Flask, jsonify, render_template, request, redirect, session
import dotenv
import requests
from .Elo import Elo
from .GameRules import GameRules

def get_site_game_local(self):
    self.supermode = "game-local"
    self.game = GameRules()

    self.beamer_make_gameimage()
    return render_template("game_local.html")

def game_local_start_round(self):
    """ Connects to the global api to pull the players elo ranking or create a new player if they dont exist yet with elo 1000. Calls GameRules.init_start to start a round of billards. 

    """
    
    res = request.json

    self.billard_api_conf = dotenv.dotenv_values(f"{self.current_dir}/config/.env")
    self.billard_api_addr = self.billard_api_conf["ADDRESS"]


    self.player = [{
        "name": res["p1"],
        "team": res["t1"],
        "elo": 1000
    },{
        "name": res["p2"],
        "team": res["t2"],
        "elo": 1000
    }]

    self.game.init_start(self.player[0], self.player[1])
    self.beamer_make_gameimage()
    
    return jsonify(self.game.display_coords)

def game_determine_start(self): # gets called two times, one time per player
    res = request.json
    print(res)
    distance = self.game.determine_start(res)#["player1"], res["player2"])
    self.beamer_make_gameimage()
    return jsonify({"player": list(res.keys())[0], "distance": distance})

def game_local_enter_round(self):
    """ This method implements the entire billard game logic for a round
    """

    # forward_coords and beamer_correct_coords both save the coords when they are called in this supermode
    coords = self.game_coords

    display_balls = self.game.enter_round(coords)

    group = self.game.groups[self.game.current_player]
    filtered = self.game.filterData(group, coords)
    if display_balls:
        self.beamer_make_gameimage(coords = filtered)
    else:
        self.beamer_make_gameimage()

    if self.game.state == "finished":
        # the game is over, somebody has won
        requests.post(f"{self.billard_api_addr}/update_local_players", json={
            "TNAME": self.billard_api_conf["TNAME"],
            "TAUTH": self.billard_api_conf["TAUTH"],
            "players": self.game.players
        })

    return jsonify({
        "current-player": self.game.get_current_player_name(),
        "remaining-balls": self.game.remaining,
        "groups": self.game.groups
        })


if __name__ == "__main__":
    data = {"1":{"a":2},"2":{"a":2}, "9":{"a":2}}
    print(filterData(0, "half", data))