import requests
import cv2
from .GameImage import GameImage
import numpy as np

# These methods mostly get called by internal functions to display the gameimage 

def beamer_push_image(self, img):
    """ Method to post an image to the beamer module to be displayed on the beamer.

    :param img: image to be posted. Will get stretched to fullscreen on the beamer.
    :type img: cv2-image
    """
    # build the url to post the image to
    beamer = self.getModuleConfig("beamer")
    #print(beamer)
    url = f"http://{beamer['ip']}:{beamer['port']}" + "/v1/receiveimage"
    #url = "http://134.28.20.50:5000/v1/receiveimage"
    #url = "http://127.0.0.1:5000/v1/receiveimage"

    _, buffer = cv2.imencode(".jpg", img)
    try:
        requests.post(url, data=buffer.tobytes(), headers={"content-type": "image/jpeg"})
    except Exception as e:
        print(e)

    print(f"Posted image to the beamer-module at {url}.")
    return "Game beamer push image"

def beamer_off(self):
    """ Method to send to and display a black image on the beamer from the beamer module.
    """
    black_image = np.zeros((1080,1920,3))
    self.beamer_push_image(black_image)

def beamer_make_gameimage(self, coords=None):
    """ Build an image with GameImage and push it to the beamer

    Handle situations like showing gameresults and instructions for modes.
    """
    gameimage = GameImage()
    
    gameimage.addGameMode(self.supermode, self)

    if coords != None:
        gameimage.placeAllBalls(coords)
    image = gameimage.getImageCV2()
    self.beamer_push_image(image)