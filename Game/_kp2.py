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
    self.kp2_prec_difficulty = 1 # 1 is regular

    self.teamtableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-teamtable.csv", header=0, sep="\t",index_col=None)
    self.fulltableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-fulltable.csv", header=0, sep="\t",index_col=None)
    self.singletableKP2 = pd.read_csv(self.current_dir + "/storage/KP2-singletable.csv", header=0, sep="\t",index_col=None)

    #print(self.teamtableKP2.to_numpy().shape)

    self.list_trickshots() # cache all the trickshots
    self.live_value = "Welcome to the final challenge!"

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

        score = max(dist) - min([5*(1+self.kp2_prec_difficulty*2)*i for i in prec]) + 500*anstoss + 500*trickshot

        timestamp = "{date:%Y-%m-%d_%H:%M:%S}".format(date=datetime.datetime.now())

        #self.teamtableKP2.loc[len(self.teamtableKP2)] = [team, score, "1"]
        self.singletableKP2.loc[len(self.singletableKP2)] = [name, team, score]
        self.fulltableKP2.loc[len(self.fulltableKP2)] = [name, team, score, anstoss, str(prec), str(dist), trickshot, timestamp, str(["no images"])]

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
    T_ind1 = copyT.copy()
    T_ind1.index += 1 # increase the index by 1 to start at 1 (= the best result is rank 1 not 0)
    copyT.columns = ["top", "mid", "bot"]
    copy = self.singletableKP2.copy()
    S_ind1 = copy.copy()
    copy.columns = ["top", "bot", "mid"]
    S_ind1.index += 1

    

    return jsonify({
		"score": score,
		"single-board": S_ind1.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		"single-podium": copy[:3].to_json(),
		"team-board": T_ind1.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
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

    self.live_value = ""

    self.beamer_make_gameimage()

    return mode

def kp2_set_precision_difficulty(self):
    """ Process and display the selected difficulty of the precision challenge
    """
    res = request.json
    self.kp2_prec_difficulty = int(res["difficulty"])

    self.beamer_make_gameimage()
    return "Updated."

def kp2_get_live_value(self):
    """ Show the score of the current try during the challenges on the beamer 
    """
    res = request.json
    match self.kp2mode:
        case "precision" | "distance":
            self.live_value = f"{res['mm']} mm"
        case "break" | "trickshot":
            self.live_value = f"{res['n']} "
    #print(self.live_value)
    self.beamer_make_gameimage(self.game_coords)
    return "Live prec"

def kp2_update_score_data_base(self):
    """ Call this method after changing the kp2_calc_score() method to update the score in each kp2 table
    
        Reads the self.fulltableKP2 pandas dataframe and updates this and the other tables based on all stored data in fulltable and the new score function
    """
    #print(self.fulltableKP2.dtypes)
    #prec = self.fulltableKP2["prec"]
    self.fulltableKP2["Score"] = self.fulltableKP2.apply(lambda x: self.kp2_calc_score(x["prec"], x["dist"], x["anstoss"], x["trickshot"]), axis=1)

    self.singletableKP2 = self.fulltableKP2[["Name", "Team", "Score"]].copy()
    self.singletableKP2 = self.singletableKP2.sort_values(by="Score", ascending=False).reset_index(drop=True)
    self.fulltableKP2 = self.fulltableKP2.sort_values(by="Score", ascending=False).reset_index(drop=True)

    self.teamtableKP2 = get_teamscores(self.singletableKP2) # already gets sorted

    self.singletableKP2.to_csv(self.current_dir + "/storage/KP2-singletable.csv", sep="\t", index=False)
    self.fulltableKP2.to_csv(self.current_dir + "/storage/KP2-fulltable.csv", sep="\t", index=False)

    self.teamtableKP2.to_csv(self.current_dir + "/storage/KP2-teamtable.csv", sep="\t",index=False)


    #print(self.fulltableKP2)
    return str(self.fulltableKP2)


###### internal 

def kp2_calc_score(self, prec, dist, anstoss, trickshot):
    """ Calculates the score based on the inputs entered by the user. Is a function as it is also used when recalculating the 
    """
    #print(type(prec), type(dist), prec.dtype)
    if type(prec) == pd.core.series.Series or type(dist) == str: # when calling this method from kp2_update_score_data_base()
        prec = [int(i) for i in strToList(prec)]
        dist = [int(i) for i in strToList(dist)]


    score = max(dist) - min([5*(1+self.kp2_prec_difficulty*2)*i for i in prec]) + 500*anstoss + 500*trickshot
    #score = max([str(i)[1:-1].split(',') for i in dist]) - min([5*(1+self.kp2_prec_difficulty*2)*str(i)[1:-1].split(",") for i in prec]) + 500*anstoss + 500*trickshot
    
    return score

def get_teamscores(df): # pass livetable
	teams = df["Team"].unique()
	teamscore = {"Team": list(teams), "Avg Score": [], "Counted": []}
	for team in teams:
		dff = df.loc[df["Team"] == team]
		n = len(dff.index)
		teamscore["Counted"].append(n)
		teamscore["Avg Score"].append(int(dff["Score"].sum()/n))
	return (pd.DataFrame(teamscore)).sort_values(by="Avg Score", ascending=False).reset_index(drop=True)

def strToList(s):
    """ Returns a list of strings from a string
    Example: '[1,2,3,4,5]' => ['1','2','3','4','5']
    """
    a = str(s)[1:-1].split(",")
    return a
