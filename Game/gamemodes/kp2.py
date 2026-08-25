import requests
from flask import request, Response
import os

from ..utils.mail_sender import send_message
from ..utils.mongo_interface import MongoDB
from ..GameImage import GameImage

from .common_utils import *
from .GameMode import GameMode
from .distance import Distance
from .precision import Precision
from .longest_break import LongestBreak
from .single_break import Break

class KP2(GameMode):
    """ This class builds upon lower level gamemodes to deliver the entire user experience for the KP2 events. The teaching unit is also known as MPD2. 
    
    .. figure:: ../images/kp2-splash.png

        The image projected when the KP2 gamemode is active, seen through the calibrated Camera Module.
    """
        
    __file__ = __file__

    def __init__(self,
            #occurences={ # THIS IS MAINLY CONTROLLED FROM kp2_config.json
            #    "precision": 5,
            #    "distance": 5,
            #    "break": 1,
            #    "longest_break": 5 # 5 starts and 2 fully to the end -> only two scores
            #},
            gm_name="KP2",
            #time=1800, # how much time students have for an attestation
            #settings=None,
            send_mails=False
        ):
        self.send_mails = send_mails

        self.gamemode_name = gm_name # "KP2"
        self.message = "Hello there :)" # this just needs to exist
        
        #self.occurences = occurences
        
        #if settings is None:
        #    self.SETTINGS = {"occurences": occurences, "time": time} # settings get unzipped in GameMode init -> time gets set to self.time
        #else:
        #    self.SETTINGS = settings

        self.SUBSELECTOR = "kp2_activity"

        self.state = "init"
        #self.active_mode = self.gamemodes[starting_mode]

        #self.longest_break_play = 5
        
        self.history_base = {} # basic history items: player, team, score, semester, attestation, mystery_challenge

        self.gameimage = GameImage()
        self.img_definiton = [ # TODO: outsource to config file?
            {
                "type": "text",
                "text": "Welcome to the MDP2 challenge! Select a gamemode"
            },
            {
                "type": "central_image",
                "img": "isem-logo-big"
            }
        ]
        self.gameimage.draw_from_dict(self.img_definiton)
        
        GameMode.__init__(self)


        # Connection to MongoDB for score calculation
        self.score_db = MongoDB(gm_name, self.config["score_aggregation"])

        self.occurences = {
            "precision": self.config["precision"],
            "distance": self.config["distance"],
            "break": self.config["break"],
            "longest_break": self.config["longest_break"]
        }

        self.GAMEMODES = {
            "distance": Distance(),
            "precision": Precision(),
            "break": Break(),
            "longest_break": LongestBreak(tries=self.occurences["longest_break"], scored=2)
        }

        self.scores = {}
        self.history_collection = {}
        for k,v in self.occurences.items():
            self.scores[k] = [None]*v
            self.history_collection[k] = {str(i): None for i in range(v)} # this direct indexing makes the pd.json_normalize easier/possible.
         

    def index_args(self):
        """ Generate a dictionary of keyword arguments that get supplied to a jinja html template of a gamemode with the same name (e.g. precision -> precision.html) in the template directory """
        out = {
            "title": "Beat the ISEM!",
            "teams": [],
            "js_vars": { # stuff that gets set as JS global variables (var declaration)
                "countdown_original_time": self.config["time"]
            }
        }
        for gm, gamemode in self.GAMEMODES.items():
            if hasattr(gamemode, "TREE"):
                html, name = gamemode.build_HTML()

                legal_name = name.lower().replace(" ", "_")
                out[legal_name + "_flow"] = html
                out[legal_name + "_results"] = list(range(self.occurences[gm]))
                #print(html)
                #print(out)
        return out

    def entrance(self, inp):
        """ Main entrance point. Mainly forwards to subgamemodes. inp must contain 'kp2_activity': 'precision' e.g. """
        activity = inp["kp2_activity"]

        out = {}
        gameimage = None
        if activity in self.GAMEMODES:
            out, gameimage, sound = self.GAMEMODES[activity].entrance(inp)
            #print("GI DEF", gameimage.definition)
            # POSTPROCESS
            real_signal = "forward"
            match out["signal"]:
                case "finished":
                    # collect the score and merge into scores dict: add new score (overwrite None value) or overwrite the smallest value
                    new_score = out["score"]

                    score_list = self.scores[activity] # list of all scores in the current activity
                    score_info = {"type": "new_score", "old_value": 0}
                    try:
                        index = score_list.index(None)
                    except: # if None is not in list: overwrite the minimum value
                        index = score_list.index(min(score_list))
                        score_info["old_value"] = min(score_list)
                        score_info["type"] = "overwrite"

                    # reset the gamemode
                    # print(f"Gamemode {activity} finished. Resetting it.")
                    #self.GAMEMODES[activity].reset() # setting friendly reset -> reset on manual request on the website
                    # immediately init the next
                    #_, gameimage = self.GAMEMODES[activity].entrance(inp)
                    self.history_collection[activity][str(index)] = self.GAMEMODES[activity].HISTORY ############################################################################

                    self.scores[activity][index] = new_score
                    out["was_round"] = index
                    #print(self.scores)
                case "interrupt": # UNUSED!!!
                    # reset the gamemode
                    self.GAMEMODES[activity].reset() # setting friendly reset
                    # immediately init the next
                    self.GAMEMODES[activity].entrance(inp)


            # change fields to not end game if a subgamemode is finished/interrupted
            out["kp2_signal"] = out["signal"]
            out["signal"] = real_signal

    
        else: # meta actions, actually for the KP2 mode not the submodes
            sound = None
            match activity:
                case "init":
                    # Draw the basic screen and wait for the user to select a gamemode
                    pass
                case "hand_in":
                    # If the final moves have been made (e.g, overwriting scores), users manually hand in their results.
                    # This triggers signal=finished
                    #out["signal"] = "finished"

                    # calculate the final score
                    #out["score"] = self.score()
                    #gameimage = self.gameimage

                    #out["hist-package"] = {"player": inp["player"], "team": inp["team"], "score": self.score}

                    out = self.hand_in()
                    print(out)
                    self.gameimage.update_text(f"Score: {out['hist-package']['score']}")
                case "settings":
                    out = self.settings(inp)

                case "debug":
                    # just immediately set the self.scores object accordingly
                    self.scores = {'precision': [np.float64(-17531.86035041569), np.float64(-17531.86035041569), np.float64(-17531.86035041569), np.float64(-17531.86035041569), np.float64(-17531.86035041569)], 'distance': [3589.642041318819, 3589.642041318819, 4438.357958681181, 4438.357958681181, 4438.357958681181], 'break': [8], 'longest_break': [0, 0, -1, -1, -1]}

                    self.history_collection = {'precision': {'0': {'distance': 1198, 'difficulty': 1}, '1': {'distance': 1198, 'difficulty': 1}, '2': {'distance': 1198, 'difficulty': 1}, '3': {'distance': 1198, 'difficulty': 1}, '4': {'distance': 1198, 'difficulty': 1}}, 'distance': {'0': {'distance': 3539, 'collisions': 1}, '1': {'distance': 4488, 'collisions': 2}, '2': {'distance': 4488, 'collisions': 2}, '3': {'distance': 7999, 'collisions': 3}, '4': {'distance': 3539, 'collisions': 1}}, 'break': {'0': {'sunk_legal': 8}}, 'longest_break': {'0': {'challenge': '1st longest break', 'decision': 'unset', 'progress': "[{'eight_sunk': False, 'white_sunk': False, 'n_sunk': 0, 'n_sunk_legal': 0, 'n_sunk_half': 0, 'n_sunk_full': 0}]", 'end_reason': 'No Ball sunk', 'sunk_legal': 0}, '1': {'challenge': '1st longest break', 'decision': 'unset', 'progress': "[{'eight_sunk': False, 'white_sunk': False, 'n_sunk': 0, 'n_sunk_legal': 0, 'n_sunk_half': 0, 'n_sunk_full': 0}]", 'end_reason': 'No Ball sunk', 'sunk_legal': 0}, '2': {'challenge': '1st longest break', 'decision': 'unset', 'progress': "[]", 'end_reason': 'logic_skip', 'sunk_legal': 0}, '3': {'challenge': '1st longest break', 'decision': 'unset', 'progress': "[]", 'end_reason': 'logic_skip', 'sunk_legal': 0}, '4': {'challenge': '1st longest break', 'decision': 'unset', 'progress': "[]", 'end_reason': 'logic_skip', 'sunk_legal': 0}}}

                    out = {"signal": "forward"}


            gameimage = self.gameimage
        
        return out, gameimage, sound


    def settings(self, inp):
        """ Handle game configuration tasks """
        settings = inp["settings"]
        out = {"signal": "forward"}

        match inp["container"]:
            case "user-info":
                self.history_base |= settings
            case "session-info":
                if self.gamemode_name == "Final Competition": return out
                self.history_base |= settings
                out["history"] = self.history(get_semester=settings["semester"])

                match int(settings["attestation"]):
                    case 1:
                        # on the first attestation, the longest break challenge is not played: create a fake (resulting in a 0 score) history. Do not do this if a longest break run has already been played 
                        if np.all([x is None for x in self.scores["longest_break"]]):
                            self.scores["longest_break"] = [0] * self.config["longest_break"] + [-1] * (self.occurences["longest_break"] - self.config["longest_break"]) 
                            out["disable"] = ["#longest_break"] # html id of the longest break section
                    case _:
                        out["enable"] = ["#longest_break"]


        return out

    def validate_config(self, config):
        return self.score_db.assert_aggregation(config["score_aggregation"])

    def hand_in(self):
        """ Calculates the total score, score breakdown and saves the history. Returns with signal="finished". """
        
        # build up the history entry
        #self.HISTORY = pd.json_normalize(self.history_base | self.history_collection).to_dict() # flatten the nested history objects
        out = {"signal": "finished"}
        self.history_addons = {}

        # check if every history is available, otherwise reset with empty specific history
        for name, gm in self.history_collection.items():
            for i, hist in gm.items():
                if hist is None:
                    self.GAMEMODES[name].reset()
                    gm[i] = self.GAMEMODES[name].HISTORY # reset the object and get the default history

        score, overview = self.get_score()
        self.history_addons["score"] = score
        self.history_addons["overview"] = overview
        out["overview"] = overview

        self.HISTORY = pd.json_normalize(self.history_base | self.history_addons | self.history_collection)
        out["hist-package"] = {k: v[0] for k,v in self.HISTORY.to_dict().items()}
        #print("KP2 OUT HIST-PACKAGE:", out["hist-package"])

        # send this runs total history by mail (addresses specified in .env)
        try:
            if self.send_mails:
                content = f"New {self.gamemode_name} results!"
                subject = f"{self.gamemode_name} results {self.HISTORY["player"][0]}, {self.HISTORY["team"][0]}"
                print("SUBJECT:", subject)
                send_message(
                    content,
                    subject, 
                    df=pd.DataFrame(self.HISTORY, index=[0]))
        except:
            print("Exception raised when trying to send mail with KP2 results.")

        return out
        


    def get_score(self):
        """ Determine the score based on the scores of the indiviual played gamemodes. Edit here to manipulate the scoring function (weights). """
        
        hist = self.history_collection | self.history_base

        precision = hist["precision"]
        distance = hist["distance"]
        single_break = hist["break"]
        longest_break = hist["longest_break"]
        
        overview = {
            "Best precision": min([x["distance"] for x in precision.values()]),
            "Best distance": max([x["distance"] for x in distance.values()]),
            "Sunken break": max([x["sunk_legal"] for x in single_break.values()]),
            "Best longest break": max([x["sunk_legal"] for x in longest_break.values()])
        }

        # turn hist from dict-dict-dict intro dict-list-dict
        h2 = {}
        for k,v in hist.items():
            if type(v) is dict:
                h2[k] = [i for i in v.values()]
            else:
                h2[k] = v

        self.score_db.enter_round(h2)
        total_score = self.score_db.get_score()

        #total_score = "tbd"

        self.score = total_score
        return total_score, overview