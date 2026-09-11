import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session, send_file
import socket
#import urllib.request
import requests
import json
import datetime
from io import BytesIO
import traceback

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

    assert "index" in inp.keys(), "The index of the gamemode object is needed."
    i = int(inp["index"])
    if not 0 <= i < len(self.GAMEMODES[selected_gamemode]) and inp["action"] != "add_instance":
        print("index to big or to small.")
        return "Index not existing.", 404

    if inp["action"] == "add_instance":
        print(f"Creating a new instance of {selected_gamemode}!")
        self.GAMEMODES[selected_gamemode].append(
            self.GAMEMODE_CLASSES[selected_gamemode]()
        )
        out = {"signal": "forward"}
        gameimage = self.GAMEMODES[selected_gamemode][-1].show()
        sound = None

        gm = self.GAMEMODES[selected_gamemode][-1]
    else:
        gm = self.GAMEMODES[selected_gamemode][i]
        # PASS TO GAMEMODE
        if inp["action"] == "show":
            out = {"signal": "forward"}
            gameimage = gm.show(inp)
            sound = None
        else:
            out, gameimage, sound = gm.entrance(inp)


    # POSTPROCESS
    # handle signal
    signal = out["signal"]
    match signal:
        case "finished":
            # The gamemode finished as intended, ran through all steps: Collect score/history
            if "hist-package" not in out.keys() and hasattr(self.GAMEMODES[selected_gamemode], "HISTORY"):
                hist = gm.history()
            else:
                hist = gm.history(add=out["hist-package"])
                del out["hist-package"] # not necessary, maybe passing it could be useful
            out["history"] = hist

            #self.GAMEMODES[selected_gamemode].reset()
            pass
        case "interrupted":
            # The gamemode finished in an alternate state (e.g. aborted)
            gm.reset()
            pass
        case "forward":
            # The gamemode is still running: forward to client, do nothing else
            pass
        # every other signal is also just forwarded


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
    raise NotImplementedError("How did you even get here??")
    gm = json_data["gmode"]
    self.GAMEMODES[gm].socket_event(json_data)


def list_available_gamemodes(self):
    """ Based on the self.GAMEMODES dict, generates a subset of gamemodes that have an gamemode.index_args() method. """
    return {k: v for k, v in self.GAMEMODES.items() if hasattr(v, "index_args")}

def get_gamemode_website(self, mode):
    """ A main level gamemode should have a website. If a gamemode exists but has no GameMode.index_args() implemented, return a 404 error. """
    if mode not in self.GAMEMODES.keys() or not hasattr(self.GAMEMODES[mode][0], "index_args"):
        return jsonify({"error": f"gamemode {mode} does not exist or does not supply a website."}), 404

    # always launch only one instance
    self.GAMEMODES[mode] = [self.GAMEMODES[mode][0]]
    self.GAMEMODES[mode][0].reset(inplace=True) # reload the gamemode to sync states with website
    gm = self.GAMEMODES[mode][0]
    index_args = gm.index_args()

    if "error" in index_args.keys():
        return index_args["error"], index_args["error_status"]
    
    # show the current gamemodes gameimage 
    self.gameimage = gm.show()
    self.gameimage.redraw()
    self.beamer.push_image(self.gameimage.getImageCV2())

    if hasattr(gm, "WEBSITE_TEMPLATE"):
        file = gm.WEBSITE_TEMPLATE
    else:
        file = mode + ".html"

    # handle non existing js_vars field
    if "js_vars" not in index_args.keys():
        index_args["js_vars"] = {}
    return self.render_template_camera(file, **(index_args | gm.history()), gamemode=mode, has_config=gm.ENABLE_CONFIG, config_slot=getattr(gm, "CONFIG_SLOT", ""))

def get_gamemode_config_website(self, mode):
    if mode not in self.GAMEMODES.keys() or (not self.GAMEMODES[mode][0].ENABLE_CONFIG):
        return jsonify({"error": f"gamemode {mode} does not exist or has no configuration options ([name]_config.json missing)"}), 404
    
    gm = self.GAMEMODES[mode][0]
    with open(gm.configuration_file, "r") as f:
        config = json.load(f)
    
    if "__active__" in config.keys():
        # this is a config with slots
        slots = json.dumps(config)

        return render_template("config_slots.html", slots=slots, name=mode)
    else:
        pretty_config = {}
        for k,v in config.items():
            pretty_config[k] = json.dumps(v, indent=4)

        return render_template("config.html", config=pretty_config, name=mode)

def write_gamemode_config(self, mode):
    if mode not in self.GAMEMODES.keys() or (not self.GAMEMODES[mode][0].ENABLE_CONFIG):
        return jsonify({"error": f"gamemode {mode} does not exist or has no configuration options ([name]_config.json missing)"}), 404

    req = request.json
    if req["password"] != os.getenv("CONFIG_PASSWORD"):
        return jsonify({"text": "Wrong password. Password is set in the .env file of the module."})

    gm = self.GAMEMODES[mode][0]
    if hasattr(gm, "validate_config") and callable(gm.validate_config):
        if "__active__" in req["config"].keys():
            slot = req["config"]["__active__"]
            accepted, message = gm.validate_config(req["config"][slot], slot=slot)
            message = "Slot " + slot + ": " + message

                #accepted = part_accepted and accepted
        else:    
            accepted, message = gm.validate_config(req["config"])

        if accepted:
            message += "\nConfig was updated. Reload the gamemodes website if currently open to apply."

    else:
        accepted = True
        message = "Config was updated. Reload the gamemodes website if currently open to apply."

    if accepted:
        try:
            #config = {}
            #for k,v in req["config"].items():
            #    config[k] = json.loads(v)
            parsed = json.dumps(req["config"], indent=4)
            with open(gm.configuration_file, "w") as f:
                f.write(parsed)
        except Exception as e:
            message = "The configuration was accepted but could not be written, as some characters are not json parsable. See the following stacktrace:\n\n" + traceback.format_exc()

    return jsonify({"text": message.replace("\n", "<br/>")})

def get_gamemode_history(self, mode):
    assert mode in self.GAMEMODES

    buffer = self.GAMEMODES[mode][0].download_history()

    print(mode, buffer)
    return send_file(buffer, download_name=f"{mode}-history.xlsx", as_attachment=True)
