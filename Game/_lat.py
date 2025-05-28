import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json
import datetime

def get_site_lat(self):
    #if request.method == "POST":
    self.teamtableLAT = pd.read_csv(self.current_dir + "/storage/LAT-teamtable.csv", header=0, sep="\t")
    self.fulltableLAT = pd.read_csv(self.current_dir + "/storage/LAT-fulltable.csv", header=0, sep="\t")
    return render_template("lat.html")

def enter_round_lat(self):
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

    self.teamtableLAT.loc[len(self.teamtableLAT)] = [team, score]
    self.fulltableLAT.loc[len(self.fulltableLAT)] = [team, score, anstoss, str(prec), str(dist), timestamp, str(["no images"])]

    #livetable_sorted = livetable.sort_values(by="Score", ascending=False).reset_index(drop=True)
    fulltable_sorted = self.fulltableLAT.sort_values(by="Score", ascending=False).reset_index(drop=True)

    #livetable_sorted.to_csv(livedata, sep="\t", index=False)
    fulltable_sorted.to_csv(self.current_dir + "/storage/LAT-fulltable.csv", sep="\t", index=False)

    #teamtable = get_teamscores(livetable_sorted)
    self.teamtableLAT.to_csv(self.current_dir + "/storage/LAT-teamtable.csv", sep="\t",index=False)
    print(score)

    copyT = self.teamtableLAT.copy()
    #copyT.columns = ["top", "mid", "bot"]
    #copy = livetable_sorted.copy()
    #copy.columns = ["top", "bot", "mid"]
    return jsonify({
		"score": score,
		#"single-board": livetable_sorted.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		#"single-podium": copy[:3].to_json(),
		"team-board": self.teamtableLAT.to_html().replace('border="1"', "").replace('style="text-align: right;"', ""),
		#"team-podium": copyT[:3].to_json()
	})