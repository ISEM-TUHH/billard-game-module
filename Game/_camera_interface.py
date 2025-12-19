import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json
import time

from .GameImage import GameImage

def forward_coords(self):
    """ Collect the coordinates from the camera module and forward it to the client

    This prevents the user from having to directly connect to the camera module. Also updates the beamer with the newly received coordinates and overlays them on the current GameImage object (self.gameimage).

    Todo:
        - Experiment with timings between turning off the beamer and taking the image (especially with playing a sound simultaneously on the beamer)
    """
    self.beamer.play_sound("please_dont_touch_the_balls")
    self.beamer_off() # project a black screen before taking the image so that the proection cant influence the Camera AI.
    time.sleep(0.3)

    res = self.camera.get_coords()
    self.beamer.play_sound("finished")

    # generate an image and place it on the beamer
    self.gameimage.update_definition({"type": "balls", "coords": res})
    self.beamer.push_image(self.gameimage.getImageCV2())

    return jsonify(res)

def camera_save_image(self):
    """ Deprecated, will raise AssertionError
    
    Save the current image and (if passed) coordinates of the balls for AI training later on 
    """
    camera = self.getModuleConfig("camera")
    api = f"http://{camera['ip']}:{camera['port']}/v1/savepic"

    assert "Old method camera_save_image (_camera_interface.py) was called. Replace with self.camera.save_image()"

    # coordinates of balls
    try:
        # may not always be defined
        coords = {"coords": self.game_coords, "action": "save-labels"}
    except:
        coords = {"action": "save-image-only"}

    response = requests.post(api, json=coords, headers={"content-type": "application/json"})
    res = response.json()
    return res
    #return "aaa"