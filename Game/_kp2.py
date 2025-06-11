import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json
import datetime

def get_site_kp2(self):
    self.supermode = "kp2"
    self.kp2mode = "base"

    self.teamtableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-teamtable.csv", header=0, sep="\t",index_col=None)
    self.fulltableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-fulltable.csv", header=0, sep="\t",index_col=None)
    self.singletableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-singletable.csv", header=0, sep="\t",index_col=None)

    print(self.teamtableKP2.to_numpy().shape)

    self.list_trickshots() # cache all the trickshots
    
    self.beamer_make_gameimage()
    return render_template("kp2.html")


def enter_round_kp2(self):
    #name = request.form.get("name")
    roundData = request.json
    if "get" not in roundData.keys():
        name = roundData["person-name"]
        team = roundData["team-name"]
        anstoss = int(roundData["break"])
        trickshot = int(roundData["trickshot"])
        prec, dist = [], []
        for i in range(1,4):
            prec.append(int(roundData[f"prec{i}"]))
            dist.append(int(roundData[f"dist{i}"]))

        score = sum(dist) - 5*min(prec) + 500*anstoss + 500*trickshot

        timestamp = "{date:%Y-%m-%d_%H:%M:%S}".format(date=datetime.datetime.now())

        #self.teamtableKP2.loc[len(self.teamtableKP2)] = [team, score, "1"]
        self.singletableKP2.loc[len(self.singletableKP2)] = [name, team, score]
        self.fulltableKP2.loc[len(self.fulltableKP2)] = [team, score, anstoss, str(prec), str(dist), timestamp, str(["no images"])]

        #self.teamtableKP2 = self.teamtableKP2.sort_values(by="Score", ascending=False).reset_index(drop=True)
        self.singletableKP2 = self.singletableKP2.sort_values(by="Score", ascending=False).reset_index(drop=True)
        self.fulltableKP2 = self.fulltableKP2.sort_values(by="Score", ascending=False).reset_index(drop=True)

        self.singletableKP2.to_csv(self.current_dir + "/storage/KP2-singletable.csv", sep="\t", index=False)
        self.fulltableKP2.to_csv(self.current_dir + "/storage/KP2-fulltable.csv", sep="\t", index=False)

        self.teamtableKP2.to_csv(self.current_dir + "/storage/KP2-teamtable.csv", sep="\t",index=False)
        print(score)


        self.kp2mode = "results" # for displaying the results on the beamer
        self.kp2_last_score = score
        self.beamer_make_gameimage()

    else:
        score = "Submit the round"

    self.teamtableKP2 = get_teamscores(self.singletableKP2)
    self.teamtableKP2.to_csv(self.current_dir + "/storage/KP2-teamtable.csv", sep="\t",index=False)
    print(score)
    
    copyT = self.teamtableKP2.copy()
    print(copyT)
    copyT.columns = ["top", "mid", "bot"]
    copy = self.singletableKP2.copy()
    copy.columns = ["top", "bot", "mid"]

    

    return jsonify({
		"score": score,
		"single-board": self.singletableKP2.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		"single-podium": copy[:3].to_json(),
		"team-board": self.teamtableKP2.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		"team-podium": copyT[:3].to_json()
	})

def select_mode_kp2(self):
    """ Based on the selected mode, build a new image and send it to the beamer.
    """
    res = request.json
    mode = res["mode"]
    self.kp2mode = mode
    print(f"KP2 mode {mode} registered.")

    if mode == "trickshot":
        self.trickshot_current_id = "0"
        self.list_trickshots()

    self.beamer_make_gameimage()

    return mode



###### internal 

def get_teamscores(df): # pass livetable
	teams = df["Team"].unique()
	teamscore = {"Team": list(teams), "Avg Score": [], "Counted": []}
	for team in teams:
		dff = df.loc[df["Team"] == team]
		n = len(dff.index)
		teamscore["Counted"].append(n)
		teamscore["Avg Score"].append(int(dff["Score"].sum()/n))
	return (pd.DataFrame(teamscore)).sort_values(by="Avg Score", ascending=False).reset_index(drop=True)
