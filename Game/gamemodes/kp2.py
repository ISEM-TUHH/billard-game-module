import requests
from flask import request, Response
import os

from ..GameImage import GameImage

from .common_utils import *
from .GameMode import GameMode
from .distance import Distance
from .precision import Precision
from .longest_break import LongestBreak
from .single_break import Break

class KP2(GameMode):
    """ This class builds upon lower level gamemodes to deliver the entire user experience for the KP2 events. The teaching unit is also known as MPD2. """

    def __init__(self, starting_mode="precision"):
        self.__file__ = __file__

        self.gamemode_name = "KP2"
        self.message = "Hello there :)" # this just needs to exist
        
        self.occurences = { # how many scores are determined for each
            "precision": 5,
            "distance": 5,
            "break": 1,
            "longest_break": 5 # 5 starts and 2 fully to the end -> only two scores
        }

        self.GAMEMODES = {
            "distance": Distance(),
            "precision": Precision(),
            "break": Break(),
            "longest_break": LongestBreak(tries=self.occurences["longest_break"], scored=2)
        }

        # index all mystery challenges here. The dictionary key gets shown on the KP2 website for selection
        self.mystery_challenges = {
            "Fantastic Four": self.mystery_distance_4b,
            "And I would walk 500 miles...": self.mystery_distance_500,
            "Not catchin' a break": self.mystery_longestbreak_break,
            "One's company, two's a crowd and three's a party": self.mystery_longestbreak_3solid,
            "Hell Yeah!": self.mystery_precision_2bull,
            "It all adds up...": self.mystery_precision_600
        }

        self.SUBSELECTOR = "kp2_activity"

        self.state = "init"
        #self.active_mode = self.gamemodes[starting_mode]

        self.longest_break_play = 5

        self.scores = {}
        self.history_collection = {}
        for k,v in self.occurences.items():
            self.scores[k] = [None]*v
            self.history_collection[k] = {str(i): None for i in range(v)} # this direct indexing makes the pd.json_normalize easier/possible.

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

    def index_args(self):
        """ Generate a dictionary of keyword arguments that get supplied to a jinja html template of a gamemode with the same name (e.g. precision -> precision.html) in the template directory """
        out = {
            "title": "Beat the ISEM!",
            "teams": ["ISEM", "Professoren", "Dekanat M"]
        }
        out["mystery_challenges"] = list(self.mystery_challenges.keys())
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
                    print(self.scores)
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
                    self.gameimage.update_text(f"Score: {out["hist-package"]['score']}")
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
                self.history_base |= settings
                self.active_mystery = settings["mystery-challenge"] # This is just the key for self.mystery_challenges dict
                out["history"] = self.history(get_semester=settings["semester"])

                match int(settings["attestation"]):
                    case 1:
                        # on the first attestation, the longest break challenge is not played: create a fake (resulting in a 0 score) history. Do not do this if a longest break run has already been played 
                        if np.all([x is None for x in self.scores["longest_break"]]):
                            self.scores["longest_break"] = [0] * self.longest_break_play + [-1] * (self.occurences["longest_break"] - self.longest_break_play) 
                            out["disable"] = ["#longest_break"] # html id of the longest break section
                    case _:
                        out["enable"] = ["#longest_break"]


        return out

    def hand_in(self):
        """ Calculates the total score, score breakdown and saves the history. Returns with signal="finished". """
        
        # build up the history entry
        #self.HISTORY = pd.json_normalize(self.history_base | self.history_collection).to_dict() # flatten the nested history objects
        out = {"signal": "finished"}
        self.history_addons = {}

        score, overview = self.get_score()
        self.history_addons["score"] = score
        self.history_addons["overview"] = overview
        out["overview"] = overview

        self.HISTORY = pd.json_normalize(self.history_base | self.history_addons | self.history_collection)
        out["hist-package"] = {k: v[0] for k,v in self.HISTORY.to_dict().items()}

        return out
        


    def get_score(self):
        """ Determine the score based on the scores of the indiviual played gamemodes. Edit here to manipulate the scoring function (weights). """

        # load history for some scoring and mystery challenge decisions/functions
        hist = self.get_history() 
        #session_hist = hist[hist["semester"].astype(str) == self.history_base["semester"] & hist["attestation"].astype(str) == self.history_base["attestation"]]
        #session_hist = hist.query(f'semester == {self.history_base["semester"]} & attestation == {self.history_base["attestation"]}')
        session_hist = hist.loc[(hist["semester"].astype(str) == self.history_base["semester"]) & (hist["attestation"].astype(str) == self.history_base["attestation"])]

        scores = self.history_collection
        #print(self.history_collection)

        precision = scores["precision"]
        distance = scores["distance"]
        single_break = scores["break"]
        longest_break = scores["longest_break"]

        # already register the maximum distance over the 5 tries in the distance challenge
        distance_distance = np.array([x["distance"] for x in distance.values()])
        self.history_addons["distance.longest"] = np.max(distance_distance)
        # closest500 is used in the mystery challenge "And I would walk 500 miles..."
        self.history_addons["distance.closest500"] = distance_distance[np.argmin(np.abs(distance_distance - 5000))]
        
        # Precision: +150p if all 5 hits are <180mm (on target)
        # Distance: +150p if at least two wall collisions on every attempt
        # Distance fancy: +250p if team has longest distance among all teams in the current competition
        # Break: +200p if sinking at least one ball
        # Longest Break: +150p pro solid, -300p pro stripe, sinking 8 ends the round with 0 points (discard if possible)
        # Other: +500p if passing attestation -> 2x precision < 180mm, 2x distance 2 walls, 2x longest break sink >=1 ball
        # Mystery challenges follow individual specifications

        overview = { # this is the actual collection of points
            "Zone 1": 0, # Precision: +50p if Zone I: <22mm (for every ball possible)
            "Two Walls": 0, # Distance: +150p if at least two wall collisions on every attempt
            "Longest Distance": 0, # Distance fancy: +250p if team has longest distance among all teams in the current competition
            "Break": 0, # Break: +200p if sinking at least one ball
            "Longest Break": 0, #Longest Break: +150p pro solid, -300p pro stripe, sinking 8 ends the round with 0 points (discard if possible)
            "Passed": 0, # Other: +500p if passing attestation -> 2x precision < 180mm, 2x distance 2 walls, 2x longest break sink >=1 ball
            "Mystery Challenge": 0,
        }
        overview["Zone 1"] = int(np.sum([50 for x in precision.values() if x["distance"] < 22]))
        overview["Two Walls"] = 150 if np.all([x["collisions"] >= 2 for x in distance.values()]) else 0
        overview["Break"] = int(np.sum([200 for x in single_break.values() if x["sunk_legal"] >= 1]))
        overview["Longest Break"] = int(np.sum([x["sunk_legal"] for x in longest_break.values() if x["decision"] == "kept"])) # calculation done in gamemode

        # Longest Distance: check if the current entry will be the final entry of the session. If true, check if it is the longest distance of all entries of the session and change the value. Otherwise, assign the 250p to the entry with the longest distance among the saved entries
        if len(session_hist) + 1 == int(self.history_base["number_teams"]):
            # if this is the final team
            updated_table = False
            max_saved_index = session_hist["distance.longest"].idxmax()
            max_saved = session_hist["distance.longest"][max_saved_index]
            if max_saved < self.history_addons["distance.longest"]:
                overview["Longest Distance"] = 250
            else:
                hist.at[max_saved_index, "overview.Longest Distance"] = 250
                hist.at[max_saved_index, "score"] += 250
                updated_table = True

            # if the mystery challenge is the 500 thing
            if self.active_mystery == "And I would walk 500 miles...":
                max_saved_index = session_hist["distance.closest500"].idxmax()
                max_saved = session_hist["distance.closest500"][max_saved_index]
                if max_saved < self.history_addons["distance.closest500"]:
                    overview["Mystery Challenge"] = 350
                else:
                    hist.at[max_saved_index, "overview.Mystery Challenge"] = 250
                    hist.at[max_saved_index, "score"] += 250
                    updated_table = True
            
            # if the table (session history) was updated, save it manually
            self.save_history(hist)

        
        # Check if passed
        passed_precision = 2 <= [x["distance"] <= 180 for x in precision.values()].count(True)
        passed_distance = 2 <= [x["collisions"] >= 2 for x in distance.values()].count(True)
        passed_longestbreak = 2 <= [x["sunk_legal"] >= 1 for x in longest_break.values()].count(True)
        overview["Passed"] = 500 if (passed_precision and passed_distance and passed_longestbreak) else 0

        # Mystery challenge
        if self.active_mystery != "And I would walk 500 miles...":
            overview["Mystery Challenge"] = self.mystery_challenges[self.active_mystery](session=scores)


        total_score = int(np.sum(list(overview.values())))
        self.score = total_score
        return total_score, overview

    #%% Mystery challenges.
    # all take the current sessions history as input and return a certain score bonus based on their requirements
    # TODO: correct exact score numbers

    def mystery_distance_4b(self, session=0, **kwargs):
        """ Fantastic Four: Hit 4 borders in (at least) one distance shot, get 350p """
        return 350 if max([x["collisions"] for x in session["distance"].values()]) >= 4 else 0
        

    def mystery_distance_500(self, session_hist=0, history_addons=0, **kwargs):
        """ And I would walk 500 miles...: Try to be the closest to 500cm in the distance shot (session wide). The closest team in the session gets 350p
        
        THIS is implemented in the KP2.score, as it manipulates the history.
        """
        return

    def mystery_precision_600(self, session=0, **kwargs):
        """ It all adds up: The accumulated distance from the bullseye over all precision shots must not be larger than 600mm, earn 350p """
        return 350 if np.sum([x["distance"] for x in session["precision"].values()]) else 0

    def mystery_precision_2bull(self, session=0, **kwargs):
        """ (2): Hit the bullseye at least twice during the precision challenge (<15mm) """
        return 350 if 2 <= [x["distance"] <= 22 for x in session["precision"].values()].count(True) else 0

    def mystery_longestbreak_3solid(self, session=0, **kwargs):
        """ One's company, two's a crowd and three's a party: Sink three solids in at least one round of the longest break """
        return 350 if np.any([x["sunk_legal"] >= 3 for x in session["longest_break"].values()]) else 0


    def mystery_longestbreak_break(self, session=0, **kwargs):
        """ Not catchin' a break: Sink at least one solid in every round of the longest break """
        return 350 if np.all([x["sunk_legal"] >= 1 for x in session["longest_break"].values()]) else 0