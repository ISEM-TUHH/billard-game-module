import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json

from .GameImage import GameImage

def forward_coords(self):
    """ Collect the coordinates from the camera module and forward it to the calling website

    This prevents the user from having to directly connect to the camera module
    """
    camera = self.getModuleConfig("camera")
    api = f"http://{camera['ip']}:{camera['port']}/v1/coords"
    response = requests.get(api)
    #print(response.json())

    # generate an image and place it on the beamer
    gameimage = GameImage(size=(2150, 1171))
    gameimage.placeAllBalls(response.json())
    image = gameimage.getImageCV2()
    self.beamer_push_image(image)

    return jsonify(response.json())