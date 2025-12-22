import numpy as np
import os
import requests
from flask import render_template, request, Response, jsonify

from ..GameImage import GameImage
from .common_utils import *
from .GameMode import GameMode

class LongestBreak(GameMode):
    """ The goal is to get the longest possible streak of sinking balls with each hit. """

    def __init__(self, data_storage=None, can_discard=True, scored=2, tries=5, round_tracker=None, can_play_on=True):
        self.__file__ = __file__

        self.gamemode_name = "Longest Break" # this is the name of the gamemode. For the template, use this to lowercase and with all spaces as _

        self.current_dir = os.path.dirname(__file__)
        self.data_storage = data_storage

        self.state = "init"
        self.finished = False
        self.score = 0
        self.sunken_legal = 0 # full/solid
        self.sunken_half = 0 # half/striped, illegal

        # setup the round tracking system since this gamemode has a ~special~ algorithm for scoring.
        if round_tracker is None:
            round_tracker = [None]*tries
        self.round_tracker = round_tracker
        self.scored = scored
        self.can_discard = can_discard
        self.can_play_on = can_play_on # if this round can be kept after the first hit

        self.last_coords = {"white": {"name": "white", "x": 100, "y": 100}}

        self.challenges = load_challenge_files(os.path.join(self.current_dir, "resources/longest_break_*.json"))
        self.active_challenge = self.challenges[0]
        self.last_coords = self.active_challenge["coordinates"]
        print(f"Longest Break: Challenges found = ({', '.join([x['name'] for x in self.challenges])}), active challenge = {self.active_challenge['name']}")

        self.HISTORY = {"challenge": self.active_challenge["name"], "decision": "unset", "progress": "[]", "end_reason": "logic_skip", "sunk_legal": 0} # progress as str due to it being able to be unset (when skipping), which would otherwise cause issues in the GameMode.history pd.concat calls (all other entries are scalar)

        self.start_geometry() # provides self.img_definition

        self.gameimage = GameImage()
        self.gameimage.draw_from_dict(self.img_definition, draw=False) # register img_definition into the GameImage object -> track and update accordingly

        self.is_first_hit = True
        self.TREE = {
            "init": [
            #    lambda inp: self.check_starting_positions(inp, starting_positions=self.active_challenge["coordinates"]),
            #    {"True": "strike", "False": "init", "skip_round": "finished"},
            #    lambda: [
            #        {
            #            "type": "balls",
            #            "coords": self.active_challenge["coordinates"],
            #            "ref": "balls-start"
            #        }
            #    ] + self.img_definition,
            #    ["Start"]
            #],
            #"strike": [
                self.determine_hit,
                {"True": "init", "False": "finished", "decide_keep": "decide_keep", "reset": "init"},
                lambda: [{
                        "type": "balls",
                        "coords": self.active_challenge["coordinates"],
                        "ref": "balls-start"
                    }] + self.img_definition,
                ["Measure"]
            ],
            "decide_keep": [
                self.decide_keep,
                {"keep": "init", "discard": "finished"},
                lambda: [{"type": "text", "text": "Keep or go to next round?"}], # keep previous definition
                [None, {
                    "type": "button",
                    "name": "keep", # this is the key in the returned json
                    "placeholder": "Keep",
                    "value": "Keep", # this gets shown to the user
                    "class": "submit-step" # this enables the JS event to submit the step on click
                },
                {
                    "type": "button",
                    "name": "discard",
                    "placeholder": "Discard",
                    "value": "Discard",
                    "class": "submit-step"
                }]
            ],
            "finished": [
                lambda x: self.setup_next_round(),
                {"False": "init"}, # not really important -> reset does that anyway. self.reset MUST NOT return True, as this would immediately skip the init step, which "proceeds" to the next step if the return is True (evaluation of return after reset...)
                lambda: [
                    {
                        "type": "text",
                        "text": f"{self.gamemode_name} Challenge: {self.message}"
                    },
                    None
                ],
                [None, {
                    "type": "button",
                    "name": "next_try",
                    "id": "next_try",
                    "placeholder": "Next Try",
                    "value": "Next Try",
                    "class": "submit-step"
                }]
            ]
        }

        GameMode.__init__(self)

    def get_score(self):
        return max(0, self.score)

    def start_game(self, inp):
        """ Sets up default values and the gameimage on the beamer, selects stored challenges """        
        # add challenge json to image base and display
        self.gameimage.draw_from_dict(self.img_definition)
        self.gameimage.update_definition({"type": "balls", "coords": self.active_challenge["coordinates"]})
        # update state to indicate readiness
        self.state = "first_hit"

        return {"signal": "forward"}

    def decide_keep(self, inp):
        """ After the first hit, the players have to decide if they want to continue this round or reset and try again """
        index = self.round_tracker.index(None)
        if "keep" == inp["clicked_on"].lower():
            self.round_tracker[index] = 0
            self.HISTORY["decision"] = "kept" # dont change, kp2.score depends on it
            return "keep", {}, {"message": "Kept"}
        #self.score = -1 # keep the score, dont remove it
        self.message = "Discarded"
        self.round_tracker[index] = "x" #-1
        self.HISTORY["decision"] = "discarded"
        return "discard", {}, {"message": f"{self.score} points", "discarded": True}

    def determine_hit(self, inp):
        """ Determines if a finished hit is valid: if a ball was sunk, stay in this state and add to score tracker, if no ball was sunk, progress to state finished """
        coords = inp["coordinates"]
        white = coords["white"]

        penalty_half = 300
        score_full = 150
        # if white sunk: end round with current points
        # and if 8 sunk: end round with 0 points

        report = coords_report(coords, self.last_coords)
        print(report)
        self.last_coords = coords

        can_hit_again = self.can_play_on #True # if the player can make another strike

        if report["eight_sunk"] and report["left_full"] > 0:
            # if the black ball was sunk: end game, 0 points
            self.score = 0
            message = "Eight Ball sunk"
            can_hit_again = False

        elif report["white_sunk"]:
            # if white ball sunk: end game, no points for the round
            message = "White Ball sunk"
            can_hit_again = False

            #return self.gameover(arg=arg)
        elif report["n_sunk_half"] > 0:
            # if an half ball was sunk: end game, minus points
            self.score -= report["n_sunk_half"] * penalty_half


            can_hit_again = False
            message = "Half Ball sunk"

            #return self.gameover(arg="half Ball sunk")
        elif report["n_sunk_full"] > 0:
            # for each full ball, add a point
            self.score += report["n_sunk_full"] * score_full
            self.sunken_legal += report["n_sunk_full"]
            message = f"Score {self.score}, hit again!"
        elif report["eight_sunk"] and report["left_full"] == 0:
            self.score += score_full
            message = "All possible balls sunk! Congrats!"
            can_hit_again = False
        else:
            # if no full ball was sunk
            can_hit_again = False
            message = "No Ball sunk"
            #return self.gameover(arg="No Ball sunk")
        # determine if a ball was sunk
        # if a full ball was sunk: +1 point
        # if no ball was sunk: end of round, RETURN

        # determine if the white ball is allowed to move
        white_move = classify_region(white, self.region_img, self.translator)
        move_line = "white_move"
        if white_move: # draw line of legal positions
            line_point = project_line(white, self.line_corners[0], self.line_corners[1])
            line_draw_end = get_border_intercept(line_point, white)
            #self.gameimage.update_definition({"type": "line", "c1": line_point, "c2": line_draw_end}, ref=move_line)
            gi_update = [{"type": "line", "c1": line_point, "c2": line_draw_end, "ref": move_line}]
        else:
            #self.gameimage.rm_definition(move_line)
            gi_update = [{"ref": move_line, "remove": True}]

        if self.is_first_hit and can_hit_again and self.can_discard:
            can_hit_again = "decide_keep"
            message = "Keep or go to next round?"
            #gi_update += [{"type": "text", "text": self.gamemode_name + ": Keep or discard?"}]
            self.is_first_hit = False
        else:
            gi_update += [{"type": "text", "text": f"{self.gamemode_name}: {message}"}]

        self.message = message

        if not "progress" in self.HISTORY.keys() or type(self.HISTORY["progress"]) is str:
            self.HISTORY["progress"] = []
        self.HISTORY["progress"].append(report) # this list will get serialized upon pd.json_normalize

        forward_returns = {"message": message}

        if not can_hit_again:
            self.HISTORY["progress"] = str(self.HISTORY["progress"])
            self.HISTORY["end_reason"] = message
            self.HISTORY["sunk_legal"] = self.score
            message = f"{self.score} points"
            forward_returns = {"message": message}

            if self.is_first_hit: # either if no ball was sunk or if this round cant continue, because it was never intended to go on beyond the first hit
                index = self.round_tracker.index(None)
                self.round_tracker[index] = "x"
                forward_returns["discarded"] = True

        local_returns = {"gameimage-updates": gi_update}
        for g in gi_update:
            self.gameimage.update_definition(g)
        if can_hit_again == True:
            local_returns["sound"] = "hell-yeah"

        return can_hit_again, local_returns, forward_returns
            
        
    def setup_next_round(self):
        """ The longest break challenge has its own method of determining rounds: there are 5 tries, but only two can be not discarded. A discard is defined by new_score=-1. This method decides, if the next round of longest_break can be discarded or not even played
        
        Returns:
            bool: can be discarded
            bool: can be played
        """
        scores = self.round_tracker
        discarded = scores.count("x")
        unplayed = scores.count(None)
        finished = scores.count(0)
        if finished == self.scored:
            next_can_discard = True
            #next_can_play = True #False
            next_can_play_on = False
        elif unplayed == self.scored - finished:
            next_can_discard = False
            #next_can_play = True
            next_can_play_on = True
        else:
            next_can_discard = True
            #next_can_play = True
            next_can_play_on = True

        print("NEXT ROUND SETUP DEBUG")
        print("next_can_discard", next_can_discard)
        print("next_can_play_on", next_can_play_on)
        print("round_tracker", self.round_tracker)
        print("finished", finished)
        print("self.scored", self.scored)


        #if not next_can_play:
        #    self.reset(inplace=True, can_discard=next_can_discard, round_tracker=self.round_tracker, scored=self.scored)
        #    self.score = -1 # already specify as discarded round
        #    return "skip_round", {}, {}
        #else:
        self.reset(inplace=True, can_discard=next_can_discard, can_play_on=next_can_play_on, round_tracker=self.round_tracker, scored=self.scored)
        return False, {}, {}


    def start_geometry(self):
        """ Provides the basic starting image. Also defines the regions according to distance defined here """
        distance = 320 #270 # distance from the green rectangle to the border: legal region. Outside the rectangle, the ball is allowed to move
        w, h = 2230, 1115
        base = [
            {
                "type": "text",
                "text": "Longest Break Challenge",
                "subimg": "isem-logo"
            },
            {
                "type": "rectangle",
                "c1": [distance, distance],
                "c2": [w - distance, h - distance],
                "outline": "green"
            }
        ]

        self.region_img = np.zeros((w, h))
        self.region_img[distance:(w-distance), distance:(h - distance)] = 150
        self.translator = {"0": True, "150": False}
        
        self.line_corners = [{"x": distance, "y": h//2}, {"x": w - distance, "y": h//2}]

        self.img_definition = base

        return base