import numpy as np

from ..GameImage import GameImage
from .common_utils import *
from .GameMode import GameMode

class Distance(GameMode):
    """ The goal is to cover the highest possible distance (including bounces of the walls) on the playing field along the horizontal axis """
    
    def __init__(self, w=2230, h=1115):
        self.__file__ = __file__

        self.gamemode_name = "Distance"
        self.state = "init"
        self.score = 0

        self.w = w
        self.h = h

        self.starting_point_raw = {
                    "x": int(0.8*w),
                    "y": h//2
                    }
        self.starting_point = {"white": {"name": "white"} | self.starting_point_raw }

        self.gameimage = GameImage(definition=[
            {
                "type": "text",
                "text": "Distance Challenge: Place the ball on the starting point",
                "subimg": "isem-logo"
            },
            {
                "type": "balls", # starting point
                "coords": self.starting_point,
                "ref": "balls-base"
            }
        ])

        self.TREE = {
            "init": [
                self.calculate_score,
                {"True": "finished"}, # no other outputs possible
                lambda: [
                    {
                        "type": "text",
                        "text": "Distance Challenge: Strike the ball!",
                        "subimg": "isem-logo"
                    },
                    {
                        "type": "balls", # starting point
                        "coords": self.starting_point,
                        "ref": "balls-base"
                    },
                    {
                        "type": "arrow_bottom",
                        "length": 300,
                        "orientation": 180,
                        "bottom": {"x": self.starting_point["white"]["x"] - 100, "y": self.starting_point["white"]["y"]},
                        "ref": "arrow-tooltip"
                    }
                ],
                ["Measure", #IDs of this button gets set to [self.gamemode_name]-[state/step (here `strike`)]-submit
                    { # special input fields needed in this step: 
                    "type": "number", # input fields are required to be changed at least once. `types` are just html input types.
                    "name": "collisions", # generates a number input field which will be available in inp["collisions"]
                    "placeholder": "Collisions", # IDs of input get set to [self.gamemode_name]-[state/step (here `strike`)]-[name]
                }]
            ],
            #"finished": [
            #    lambda x: self.reset(inplace=True),
            #    {"False": "init"}, # not really important -> reset does that anyway
            #    lambda: [
            #        {
            #            "type": "text",
            #            "text": f"{self.gamemode_name} Challenge: {self.message}"
            #        }
            #    ],
            #    ["Next try"]
            #]
        }

        GameMode.__init__(self)
        

    def entrance_old(self, inp): # normally overloads GameMode.entrance
        """ init -> register start -> [shoot and enter # of border collisions, user clicks enter] -> calculate distance (finish) """

        match self.state:
            case "init":
                out = {"signal": "forward"}
                self.state = "check_placement"
            case "check_placement":
                # TODO: integrate a check that only one ball exists? -> done in check_positions
                out = {"signal": "forward"}
                coords = inp["coordinates"]#["white"]
                within_tolerance, message, signal_coords = check_positions(inp["coordinates"], [self.starting_point_raw])
                if within_tolerance:
                #if is_close_enough(coords, self.starting_point["white"]):
                    self.gameimage.update_text("Distance Challenge: Now strike the ball!")
                    self.gameimage.update_definition({"type": "balls", "coords": self.starting_point}, ref="ball-base") # if that has been written to during the correction loop
                    self.gameimage.update_definition({
                        "type": "arrow_bottom",
                        "length": 300,
                        "orientation": 180,
                        "bottom": {"x": self.starting_point["white"]["x"] - 100, "y": self.starting_point["white"]["y"]},
                        "ref": "arrow-tooltip"
                    })
                    self.state = "waiting_measurement"
                    out["message"] = "Strike and enter collisions"

                else:
                    self.gameimage.update_text(f"Distance Challenge: {message}")
                    # show coordinate of falsely placed ball (output of check_positions)
                    new_coordinates_field = {"type": "balls", "coords": signal_coords}
                    self.gameimage.update_definition(new_coordinates_field)
                    out["message"] = "Try again"

            case "waiting_measurement":
                self.score = self.calculate_score(inp)
                self.gameimage.update_text(f"Distance Challenge: {(self.score/1000):.2f} m")
                out = {"signal": "finished", "score": self.score, "message": f"{(self.score/1000):.2f} m"}

        return out, self.gameimage.copy()

    def place_ball(self, inp):
        """ Checks if the ball is placed on the starting point. Returns True if it is correct, False if not. """
        # TODO: integrate a check that only one ball exists? -> done in check_positions
        #out = {"signal": "forward"}
        coords = inp["coordinates"]#["white"]
        within_tolerance, message, signal_coords = check_positions(inp["coordinates"], [self.starting_point_raw])
        
        return within_tolerance, {"gameimage-updates": [{"type": "balls", "coords": signal_coords}, {"type": "text", "text": f"{self.gamemode_name} Challenge: {message}"}]}, {"message": message} 

    def calculate_score(self, inp):
        """ Horizontal distance in mm is the score """
        collisions = int(inp["collisions"])
        
        # ugly formula, if you want to understand it, draw the distance covered for 0 to 3 collisions on a piece of paper
        border_distance = int(collisions/2)*2*self.w
        start_bias = self.starting_point_raw["x"]
        final_distance = list(inp["coordinates"].values())[0]["x"] * (-1+2*(collisions%2))

        distance = border_distance + final_distance + start_bias
        self.distance = distance

        self.HISTORY = {"distance": int(distance), "collisions": collisions}

        self.score = distance
        self.message = f"{(self.distance/1000):.2f} m"
        return True, {}, {"message": self.message}