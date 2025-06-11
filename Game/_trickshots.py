from .GameImage import Trickshot

import cv2
import numpy as np
import glob # for finding all .json files
import os
import json
from flask import jsonify, render_template, request

def get_site_trickshots(self):
    self.supermode = "trickshots"
    self.beamer_make_gameimage()
    return render_template("trickshots.html")

def list_trickshots(self):
    """ List all trickshots saved in trickshots/ with their name, description and difficulty (and if they are compatible with this table size).
 
    """
    crawlPath = os.path.join(self.current_dir, "trickshots/*.json")
    files = glob.glob(crawlPath)
    self.trickshots = {}
    send_trickshots = []

    idT = 0
    for f in files:
        with open(f, "r") as file:
            trickshot = json.load(file)
            trickshot["id"] = idT

            condensed = {
                "name": trickshot["name"],
                "difficulty": trickshot["difficulty"],
                "description": trickshot["description"], # doesnt display the description on the website yet
                "compatible": (trickshot["size"] == self.config["size"]),
                "id": trickshot["id"]
            }

            send_trickshots.append(condensed)
            self.trickshots[str(idT)] = trickshot
            
            idT += 1

    return jsonify(send_trickshots)

def load_trickshot(self):
    """ Load a single trickshot into the beamer. Name, description and difficulty are already loaded and should be displayed by the frontend
    """
    if "request" in locals():    
        res = request.json
    else:
        res = {"id": "0"}
        self.list_trickshots()
    #print(res)
    self.trickshot_current_id = res["id"]
    # retrieve the trickshot from all the loaded trickshots
    trickshot_definition = self.trickshots[str(res["id"])] 
    print(trickshot_definition["id"], res)

    trickshot = Trickshot(trickshot_definition)
    img = trickshot.getTrickshotImageCV2()

    self.beamer_push_image(img)
    # name, description and difficulty are already loaded and displayed inside the frontend
    
    return "Success i hope."


# -------------- Functions to generate trickshots ------------------------
def get_site_create_trickshots(self):
    return render_template("create_trickshots.html")