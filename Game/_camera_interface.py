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
    """ Collect the coordinates from the camera module and forward it to the calling website

    This prevents the user from having to directly connect to the camera module. Also updates the beamer with a current game image and overlays depending on the current mode.
    """
    self.beamer_off() # project a black screen before taking the image so that the proection cant influence the Camera AI.
    time.sleep(1.5)
    
    camera = self.getModuleConfig("camera")
    api = f"http://{camera['ip']}:{camera['port']}/v1/coords"
    response = requests.get(api)
    res = response.json()

    # generate an image and place it on the beamer
    self.beamer_make_gameimage(coords = res)

    return jsonify(res)