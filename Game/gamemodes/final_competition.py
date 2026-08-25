from .kp2 import KP2
import numpy as np

class FinalCompetition(KP2):
    """ This is an abstraction of the KP2 mode. It essentially is the same, only using a different number of challenges and allows for the input of previously collected bonus points. It is used in the final competition of the KP2/MDP2 project.

    """
    def __init__(self, settings=None):
        self.__file__ = __file__

        #occurences = {
        #    "precision": 2,
        #    "distance": 2,
        #    "break": 0,
        #    "longest_break": 0
        #}

        KP2.__init__(self, gm_name="Final Competition") # super init

        self.WEBSITE_TEMPLATE = "kp2.html"

        self.img_definition = [ # TODO: outsource to config file?
            {
                "type": "text",
                "text": "Welcome to the Agile Design Lab!"#"Welcome to the final competition! Select a gamemode"
            },
            {
                "type": "central_image",
                "img": "isem-logo-big"
            }
        ]
        self.gameimage.draw_from_dict(self.img_definition)

    def get_score(self):
        """ Determine the score based on the scores of the indiviual played gamemodes. Edit here to manipulate the scoring function (weights).
        
        This is a clone of KP2.get_score, except that it does not account for Mystery Challenges or Passing
        
        """

        # load history for some scoring and mystery challenge decisions/functions
        hist = self.get_history() 
        #session_hist = hist[hist["semester"].astype(str) == self.history_base["semester"] & hist["attestation"].astype(str) == self.history_base["attestation"]]
        #session_hist = hist.query(f'semester == {self.history_base["semester"]} & attestation == {self.history_base["attestation"]}')
        if len(hist) != 0:
            session_hist = hist#.loc[(hist["semester"].astype(str) == self.history_base["semester"]) & (hist["attestation"].astype(str) == self.history_base["attestation"])]
        else:
            session_hist = hist

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
        # save the minimal distance from 500cm in mm.
        self.history_addons["distance.closest500"] = np.abs(distance_distance[np.argmin(np.abs(distance_distance - 5000))] - 5000)
        
        # Precision: +150p if all 5 hits are <180mm (on target)
        # Distance: +150p if at least two wall collisions on every attempt
        # Distance fancy: +250p if team has longest distance among all teams in the current competition
        # Break: +200p if sinking at least one ball
        # Longest Break: +150p pro solid, -300p pro stripe, sinking 8 ends the round with 0 points (discard if possible)

        overview = { # this is the actual collection of points
            #"Zone 1": 0, # Precision: +50p if Zone I: <22mm (for every ball possible)
            #"Two Walls": 0, # Distance: +150p if at least two wall collisions on every attempt
            #"Longest Distance": 0, # Distance fancy: +250p if team has longest distance among all teams in the current competition
            #"Break": 0, # Break: +200p if sinking at least one ball
            #"Longest Break": 0, #Longest Break: +150p pro solid, -300p pro stripe, sinking 8 ends the round with 0 points (discard if possible)
            #"Passed": 0, # Other: +500p if passing attestation -> 2x precision < 180mm, 2x distance 2 walls, 2x longest break sink >=1 ball
            #"Mystery Challenge": 0,
        }
        #overview["Zone 1"] = int(np.sum([50 for x in precision.values() if x["distance"] < 22]))
        #overview["Two Walls"] = 150 if np.all([x["collisions"] >= 2 for x in distance.values()]) else 0

        overview["Best Precision"] = min([x["distance"] for x in precision.values()])
        overview["Best Distance"] = max([x["distance"] for x  in distance.values()])
        overview["Score"] = overview["Best Distance"] - 3*overview["Best Precision"]

        # THIS IS COMMENTED FOR THE INAUGURAL LECTURE! As we dont play a single break in the example challenge
        #overview["Break"] = int(np.sum([200 for x in single_break.values() if x["sunk_legal"] >= 1]))
        
        #overview["Longest Break"] = int(np.sum([x["sunk_legal"] for x in longest_break.values()]))# if x["decision"] == "kept"])) # calculation done in gamemode

        # Longest Distance: check if the current entry will be the final entry of the session. If true, check if it is the longest distance of all entries of the session and change the value. Otherwise, assign the 250p to the entry with the longest distance among the saved entries
        if False:# and len(session_hist) + 1 == int(self.history_base["number_teams"]):
            # if this is the final team
            updated_table = False
            
            if len(session_hist) == 0:
                # if there is only one team in the attestation (mainly when testing aahhh)
                max_saved = -1000000
            else:
                max_saved_index = session_hist["distance.longest"].idxmax()
                max_saved = session_hist["distance.longest"][max_saved_index]
            if max_saved < self.history_addons["distance.longest"]:
                overview["Longest Distance"] = 250
            else:
                hist.at[max_saved_index, "overview.Longest Distance"] = 250
                hist.at[max_saved_index, "score"] += 250
                updated_table = True
            
            # if the table (session history) was updated, save it manually
            self.save_history(hist)


        total_score = overview["Score"]#int(np.sum(list(overview.values())))
        self.score = overview["Score"]#total_score
        return total_score, overview

    def index_args(self):
        """ Generate a dictionary of keyword arguments that get supplied to a jinja html template of a gamemode with the same name (e.g. precision -> precision.html) in the template directory """
        out = {
            "title": "Schlag das ISEM!",
            "teams": [],
            "js_vars": { # stuff that gets set as JS global variables (var declaration)
                #"countdown_original_time": self.time
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