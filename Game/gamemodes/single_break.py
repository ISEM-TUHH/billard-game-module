from .common_utils import *
from ..GameImage import GameImage
from .GameMode import GameMode

import pandas as pd

class Break(GameMode):
    """ The goal is to sink as many balls as possible with a single hit """
    
    def __init__(self):
        self.__file__ = __file__

        self.gamemode_name = "Break"
        self.state = "init"
        self.score = 0

        self.gameimage = GameImage()
        #self.gameimage.draw_from_dict([
        #                            {
        #                                "type": "text",
        #                                "text": "Break Challenge",
        #                                "subimg": "isem-logo"
        #                            },
        #                            {
        #                                "type": "break",
        #                                "draw_ball": True
        #                            }
        #                        ])

        self.TREE = {
            "init": [
                self.count,
                {"finished": "finished", "False": "init", "reset": "init"}, # the last must be a loop due to reset dynamics
                lambda: [
                    {
                        "type": "text",
                        "text": "Break Challenge",
                        "subimg": "isem-logo"
                    },
                    {
                        "type": "break",
                        "draw_ball": True
                    }
                ],
                ["Count sunk balls"]
            ]
        }
                                
        GameMode.__init__(self)

    def count(self, inp):
        coords_old = {v: 1 for v in ALL_BALLS} # ALL_BALLS imported from common_utils: list of all names
        coords = inp["coordinates"]
        report = coords_report(coords, coords_old)

        self.score = report["n_sunk_legal"] # dont just shoot the white ball into a hole
        self.HISTORY = {
            "sunk_legal": self.score,
            "start_time": pd.Timestamp.now()
        }
        #self.state = "finished"
        out = {"signal": "finished", "score": self.score}

        self.message = f"{self.score} balls sunk"
        return "finished", {}, {"message": self.message}

    def entrance_old(self, inp):

        match self.state:
            case "init":
                out = {"signal": "forward"}
                self.state = "hit"
            case "hit":
                coords_old = {v: 1 for v in ALL_BALLS} # ALL_BALLS imported from common_utils: list of all names
                coords = inp["coordinates"]
                report = coords_report(coords, coords_old)

                self.score = report["n_sunk_legal"] # dont just shoot the white ball into a hole
                self.HISTORY = {"sunk_legal": self.score}
                self.state = "finished"
                out = {"signal": "finished", "score": self.score}

        return out, self.gameimage.copy()