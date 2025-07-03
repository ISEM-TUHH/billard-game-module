import dotenv
import requests
import json
from flask import Flask, jsonify, render_template, request, redirect, session
import numpy

def get_site_game_online(self):
    self.billard_api_conf = dotenv.dotenv_values(f"{self.current_dir}/config/.env")
    self.billard_api_addr = self.billard_api_conf["ADDRESS"]
    self.all_tables = requests.get(f"{self.billard_api_addr}/all_tables_json").json()

    notification = ""
    if request.method == "POST" and "mode" not in request.form.keys():
        # register a new player
        print(request.form)
        info = dict(request.form)
        info["public"] = "public" in info.keys()
        requests.post(f"{self.billard_api_addr}/add_player", json={
            "TNAME": self.billard_api_conf["TNAME"],
            "TAUTH": self.billard_api_conf["TAUTH"],
            "TPOS": self.billard_api_conf["TPOS"],
            "player-info": info
        })
        notification = f"New player registered: {info['name']}"

    return render_template("game_online.html", table_list=self.all_tables, notification=notification)

def get_site_register_player(self):
    return render_template("register_player.html")


def online_start_game(self):
    res = request.json

    TAUTH = self.billard_api_conf["TAUTH"]
    TNAME = self.billard_api_conf["TNAME"]
    PNAME = res["PNAME"]
    PAUTH = res["PAUTH"]

    res1 = requests.post(f"{self.billard_api_addr}/start_game", json={
        "TNAME": TNAME,
        "TAUTH": TAUTH,
        "PNAME": PNAME,
        "PAUTH": PAUTH,
        "TID2": res["TID2"],
    })
