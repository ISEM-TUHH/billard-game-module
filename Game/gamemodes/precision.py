import numpy as np
import requests
from flask import render_template, request, Response, jsonify

from ..GameImage import GameImage
from .common_utils import *
from .GameMode import GameMode

class Precision(GameMode):
    """ The goal is to get as close as possible to the projected bullseye. """

    def __init__(self, data_storage="", bullseye=[2230//4, 1115//2], settings={"difficulty": 0}):
        self.__file__ = __file__

        self.gamemode_name = "Precision"
        
        self.data_storage = data_storage
        self.bullseye_center = bullseye

        self.SETTINGS = settings
        self.difficulty = int(settings["difficulty"])
        self.penalty_factor = lambda: 5*(1+2*self.difficulty) # TODO: rework this formula

        self.state = "init"
        self.finished = False
        self.score = 0

        self.last_coords = {}

        self.gameimage = GameImage()
        self.gameimage.draw_from_dict(self.start_geometry(default_difficulty=self.difficulty), draw=False)

        self.TREE = {
            "init": [
            #    lambda inp: self.check_starting_positions(inp, starting_positions=lambda: [self.start_points[int(self.difficulty)]], update_gameimage=self.gameimage),
            #    {"True": "strike", "False": "init"},
            #    lambda: self.gameimage.definition,
            #    ["Start"]
            #],
            #"strike": [
                self.determine_precision,
                {"True": "finished", "reset": "init"},
                lambda: self.gameimage.definition,
                ["Measure"]
            ]
        }

        GameMode.__init__(self)


    def settings(self, inp):
        """ Handle setting requests. In this gamemode, this is only the difficulty (0 = hard, 1, 2=easy) """
        print("Updating settings with", inp)
        settings = inp["settings"]
        self.SETTINGS = settings
        self.difficulty = int(settings["difficulty"])
        for i in range(3):
            self.gameimage.update_definition(3 if i != self.difficulty else 7, ref=f"difficulty-{i}", subfield="width")
            self.gameimage.update_definition({"white": {"name": "white"} | self.start_points[self.difficulty]}, ref="balls-start", subfield="coords")

        return {}, {"message": f"x{self.penalty_factor()}"} # this is what gets put on the label
        #return {"signal": "forward", "penalty": self.penalty_factor()}


    def determine_precision(self, inp):
        """ Determines if a finished hit is valid: if a ball was sunk, stay in this state and add to score tracker, if no ball was sunk, progress to stafte finished """
        if len(inp["coordinates"].values()) == 0:
            return False, {"gameimage-updates": [{"type": "text", "text": "No ball found, try again!"}]}, {"message": "No ball found."}
            
        coords = inp["coordinates"]
        #ball = [v for v in coords.items()][0]

        # determine the distance between a ball and the center of the bullseye
        ball, dist = metric_distance_closest(coords, vec_to_coord(self.bullseye_center))

        self.HISTORY = {"distance": int(dist), "difficulty": self.difficulty}

        self.score = -dist * self.penalty_factor() # TODO: rework this formula
        self.message = f"{int(dist)} mm"
        return True, {}, {"message": self.message}
        #return {"signal": "finished", "message": f"{int(dist)} mm", "score": int(self.score)}



    def start_geometry(self, default_difficulty=1):
        """ Provides the basic starting image. Also defines the regions according to distance defined here """
        distance = 200
        w, h = 2230, 1115
        base = [
            {
                "type": "text",
                "text": "Precision Challenge",
                #"subimg": "isem-logo"
            },
            {
                "type": "bullseye",
                "center": self.bullseye_center
            }
        ]
        lines = [w-250, w-500, w-750]
        self.start_points = [{"x": x, "y": h//2} for x in lines]
        for i in range(3):
            # 0,1,2
            base.append({
                "type": "line",
                "c1": [lines[i], 100],
                "c2": [lines[i], h-100],
                "width": 7 if i == default_difficulty else 3,
                "ref": "difficulty-" + str(i)
            })
        base.append({
            "type": "balls",
            "coords": {"white": {"name": "white"} | self.start_points[default_difficulty]},
            "ref": "balls-start"
        })

        #self.region_img = np.zeros((w, h))
        #self.region_img[distance:(w-distance), distance:(h - distance)] = 150
        #self.translator = {"0": True, "150": False}
        
        #self.line_corners = [{"x": distance, "y": h//2}, {"x": w - distance, "y": h//2}]

        self.img_definition = base

        return base