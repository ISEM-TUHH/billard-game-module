import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json

def get_site_kp2(self):
    self.supermode = "kp2"
    self.kp2mode = "base"

    self.teamtableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-teamtable.csv", header=0, sep="\t")
    self.fulltableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-fulltable.csv", header=0, sep="\t")

    self.list_trickshots() # cache all the trickshots
    if request.method == "POST":
        return render_template("kp2.html")


def enter_round_kp2(self):
    #name = request.form.get("name")
    roundData = request.json
    team = roundData["team"]
    anstoss = int(roundData["break"])
    prec, dist = [], []
    for i in range(1,4):
        prec.append(int(roundData[f"prec{i}"]))
        dist.append(int(roundData[f"dist{i}"]))

    score = sum(dist) - 5*min(prec) + 500*anstoss

    timestamp = "{date:%Y-%m-%d_%H:%M:%S}".format(date=datetime.datetime.now())

    self.teamtableKP2.loc[len(self.teamtableKP2)] = [team, score]
    self.fulltableKP2.loc[len(self.fulltableKP2)] = [team, score, anstoss, str(prec), str(dist), timestamp, str(["no images"])]

    #livetable_sorted = livetable.sort_values(by="Score", ascending=False).reset_index(drop=True)
    fulltable_sorted = self.fulltableKP2.sort_values(by="Score", ascending=False).reset_index(drop=True)

    #livetable_sorted.to_csv(livedata, sep="\t", index=False)
    fulltable_sorted.to_csv(self.current_dir + "/storage/KP2-fulltable.csv", sep="\t", index=False)

    #teamtable = get_teamscores(livetable_sorted)
    self.teamtableKP2.to_csv(self.current_dir + "/storage/KP2-teamtable.csv", sep="\t",index=False)
    print(score)

    copyT = self.teamtableKP2.copy()
    #copyT.columns = ["top", "mid", "bot"]
    #copy = livetable_sorted.copy()
    #copy.columns = ["top", "bot", "mid"]
	
    self.kp2mode = "results" # for displaying the results on the beamer

    return jsonify({
		"score": score,
		#"single-board": livetable_sorted.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		#"single-podium": copy[:3].to_json(),
		"team-board": self.teamtableKP2.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		#"team-podium": copyT[:3].to_json()
	})

def select_mode_kp2(self):
    """ Based on the selected mode, build a new image and send it to the beamer.
    """
    res = request.json
    mode = res["mode"]
    self.kp2mode = mode
    print(f"KP2 mode {mode} registered.")

    self.beamer_make_gameimage()

    return mode