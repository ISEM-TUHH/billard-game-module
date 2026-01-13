import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json
import datetime

""" This file provides methods necessary for the implementation of the MVC model for running gamemodes """

def gamemode_controller(self):
    """ This method receives the posted data to the common gamemode API endpoint (`/gamemodecontroller`)
    - preprocess: select gamemode
    - passes it to the selected gamemode object (entrance(...) method, most of the times inherited from GameMode)
    - postprocess: update gameimage, send to beamer, read signal in output (handle), return output
    
    """
    inp = request.json
    #print("Input to the game module:", inp)

    # If the inp contains coordinates, they are assumed to be correct. Order the camera module to save its previously cached image with the coordinates for training in the future.
    if "coordinates" in inp.keys():
        self.camera.save_cached_image_training(inp["coordinates"])

    # PREPROCESS: select gamemode
    assert "gmode" in inp.keys(), f"gamemode not found in input, keys: {inp.keys()}"
    selected_gamemode = inp["gmode"]
    assert selected_gamemode in self.GAMEMODES.keys(), f"selected gamemode {selected_gamemode} not found in registered gamemodes: {self.GAMEMODES.keys()}"

    # PASS TO GAMEMODE
    if inp["action"] == "show":
        out = {"signal": "forward"}
        gameimage = self.GAMEMODES[selected_gamemode].show(inp)
        sound = None
    else:
        out, gameimage, sound = self.GAMEMODES[selected_gamemode].entrance(inp)


    # POSTPROCESS
    # handle signal
    signal = out["signal"]
    match signal:
        case "finished":
            # The gamemode finished as intended, ran through all steps: Collect score/history
            if "hist-package" not in out.keys() and hasattr(self.GAMEMODES[selected_gamemode], "HISTORY"):
                hist = self.GAMEMODES[selected_gamemode].history()
            else:
                hist = self.GAMEMODES[selected_gamemode].history(add=out["hist-package"])
                del out["hist-package"] # not necessary, maybe passing it could be useful
            out["history"] = hist

            #self.GAMEMODES[selected_gamemode].reset()
            pass
        case "interrupted":
            # The gamemode finished in an alternate state (e.g. aborted)
            self.GAMEMODES[selected_gamemode].reset()
            pass
        case "forward":
            # The gamemode is still running: forward to client, do nothing else
            pass


    # play the sound if specified
    if not sound is None:
        self.beamer.play_sound(sound)

    # send gameimage to the Beamer
    self.gameimage = gameimage # make available to other methods like the API interface to update the text

    self.gameimage.redraw()
    self.beamer.push_image(self.gameimage.getImageCV2())

    # RETURN RESPONSE
    return jsonify(out)

def gamemode_socket_handler(self, json_data):
    """ This function forwards events on the "gamemode-socket" socket to the specified gamemode. 

    A gamemode must have a GameMode.SOCKETS dictionary matching the current state to a message handler like {"init": self.handler}
    """
    gm = json_data["gmode"]
    self.GAMEMODES[gm].socket_event(json_data)


def list_available_gamemodes(self):
    """ Based on the self.GAMEMODES dict, generates a subset of gamemodes that have an gamemode.index_args() method. """
    return {k: v for k, v in self.GAMEMODES.items() if hasattr(v, "index_args")}

def get_gamemode_website(self, mode):
    """ A main level gamemode should have a website. If a gamemode exists but has no GameMode.index_args() implemented, return a 404 error. """
    if mode not in self.GAMEMODES.keys() or not hasattr(self.GAMEMODES[mode], "index_args"):
        return jsonify({"error": f"gamemode {mode} does not exist or does not supply a website."}), 404

    self.GAMEMODES[mode].reset(inplace=True) # reload the gamemode to sync states with website
    
    # show the current gamemodes gameimage 
    self.gameimage = self.GAMEMODES[mode].show()
    self.gameimage.redraw()
    self.beamer.push_image(self.gameimage.getImageCV2())

    if hasattr(self.GAMEMODES[mode], "WEBSITE_TEMPLATE"):
        file = self.GAMEMODES[mode].WEBSITE_TEMPLATE
    else:
        file = mode + ".html"
    return self.render_template_camera(file, **(self.GAMEMODES[mode].index_args() | self.GAMEMODES[mode].history()))
