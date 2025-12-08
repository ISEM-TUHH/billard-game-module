from pathlib import Path
import pandas as pd
import json
from ..GameImage import GameImage
from .common_utils import *

class GameMode:
    """ The parent class to all gamemodes. Provides common implementations like show and history management 

    """

    def __init__(self):
        self.score = 0
        self.state = "init"
        self.name = Path(self.__file__).stem
        self.history_file = Path(self.__file__).parent.absolute().joinpath(Path("resources"), self.name + "_history.csv")
        if hasattr(self, "HISTORY_FORMAT") and self.HISTORY_FORMAT == ".json":
            # for very sparse data it can be reasonable to write a more comprehensive history into a .json file -> see GameMode.save_json_history
            # A boiled down history can still be saved into the .csv file
            self.json_history_file = Path(self.__file__).parent.absolute().joinpath(Path("resources"), self.name + "_history.json")
        #print("History file: ", self.history_file)
        #self.gameimage = GameImage()
        if not hasattr(self, "HISTORY"):
            self.HISTORY = {} # history objects of this current round/instance
        
        # the "finished" action is always the same. If not defined, this is the default.
        # the previous method must set self.message and the child class must have an attribute self.gamemode_name
        if hasattr(self, "TREE"):
            if "finished" not in self.TREE.keys():
                self.TREE["finished"] = [
                        lambda x: self.reset(inplace=True),
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
            #print(self.gamemode_name, "TREE setup with keys", list(self.TREE.keys()))

    def entrance(self, inp):
        """ Using self.TREE, determine the next actions. """
        out = {}
        sound = None

        print("Input from client:", inp.keys())

        if inp["action"] == "settings":
            local_returns, forward_returns = self.settings(inp)
            new_state = self.state
            
        else:
            progress_decider, local_returns, forward_returns = self.TREE[self.state][0](inp)
            #print(progress_decider, self.TREE[self.state][1])

            new_state = self.TREE[self.state][1][str(progress_decider)]

            new_gameimage_lambda = self.TREE[new_state][2]
            if new_gameimage_lambda is not None:
                self.gameimage.draw_from_dict(new_gameimage_lambda(), draw=False) # just update definiton, dont draw -> this gets done by the controller one level above

        if "sound" in local_returns.keys():
            sound = local_returns["sound"]
        elif self.state != new_state: # when there is a new state, signal progress
            sound = "finished"

        if self.state == new_state:
            if "reset-gameimage" in local_returns.keys() and local_returns["reset-gameimage"]:
                self.gameimage.definition = [] # completely reset the gameimage, draw the new stuff from zero
            if "gameimage-updates" in local_returns.keys():
            #if "gameimage-updates" in local_returns.keys():
                # if there is no new state: add other returns
                for element in local_returns["gameimage-updates"]:
                    ref = element["ref"] if "ref" in element.keys() else None
                    self.gameimage.update_definition(element, ref=ref)

            
        
        print("GAMEMODE", self.name, self.state, "->", new_state)
        self.state = new_state

        out |= forward_returns
        out["signal"] = self.state # the gamemode must end in "finished" -> the input region named [self.gamemode_name]-[self.state] will get activated, all other disabled.
        out["score"] = self.score

        #print(self.gameimage.definition)
        return out, self.gameimage, sound

    def socket_event(self, json_data):
        """ Using self.SOCKETS handle the socket event. """
        if hasattr(self, "SOCKETS") and self.state in self.SOCKETS.keys():
            self.SOCKETS[self.state](json_data)


    def show(self, inp={}):
        """ When (re)entering the gamemode, determine what gameimage to show.
        
        If the gamemode contains children gamemodes, they must be organized in a dictionary named self.GAMEMODES with the key self.SUBSELECTOR in the input inp selecting the child gamemode by key of the dictionary. 
        """
        if self.state == "init":
            if hasattr(self, "GAMEMODES") and inp != {}: # if this object has subelements
                #print("KP2 inp show:", inp)
                if inp[self.SUBSELECTOR] not in self.GAMEMODES: # some kind of gamemode that is not outsourced
                    return self.gameimage.copy()
                gameimage = self.GAMEMODES[inp[self.SUBSELECTOR]].show(inp)
            else:
                if hasattr(self, "TREE"):
                    #print("Subelement of KP2 inp show:", inp)
                    self.gameimage.draw_from_dict(self.TREE[self.state][2](), draw=False)
                    gameimage = self.gameimage
                else:
                    #print("Show called with entrance(inp) on", self.name)
                    gameimage = self.gameimage
                    #out, gameimage = self.entrance(inp)
        else:
            gameimage = self.gameimage.copy()
        return gameimage


    def reset(self, keep_settings=True, inplace=False, **kwargs):
        """ Reset the gamemode object but keep changes made to the settings. If reset inplace, overwrite this itself """
        if hasattr(self, "SETTINGS") and keep_settings:
            if inplace:
                self.__init__(settings=self.SETTINGS, **kwargs)
                print("Reset this object. New state:", self.state)
                return False, {}, {}
                
            return self.__init__(settings=self.SETTINGS, **kwargs)

        if inplace:
            self.__init__(**kwargs)
            print("Reset this object. New state:", self.state)
            return False, {}, {}
        return self.__init__(**kwargs)

    def get_history(self):
        if self.history_file.exists():
            hist = pd.read_csv(self.history_file, sep="\t", index_col=False)
        else:
            hist = pd.DataFrame()
        return hist

    def save_history(self, history):
        history.to_csv(self.history_file, sep="\t", index=False)

    def save_json_history(self, history):
        entire_history = []
        with open(self.json_history_file, "r") as file:
            entire_history = json.load(file)
        entire_history.append(history)
        with open(self.json_history_file, "w") as file:
            json.dump(entire_history, file, ensure_ascii=False, indent=4)

    def history(self, history=None, add=None, get_semester=None):
        """ Get the player/team rankings and podium. Returns a dictionary that can be used to generate html code for showing the list and podium. History files are organized inside the `ressources` directory, always starting with the stem of the gamemode filename (kp2.py -> kp2_...). History file must be name [gamemode]_history.csv.
        If adding to the history, set add to a dictionary containing all fields you want to save (must contain `player`, `team` and `score`). A timestamp automatically gets added.
        """
        if history is None:
            if self.history_file.exists():
                hist = pd.read_csv(self.history_file, sep="\t", index_col=False)
            else:
                hist = pd.DataFrame()
                if add is None: return {}
        else:
            hist = history

        if add is not None:
            add["timestamp"] = pd.Timestamp.now()
            if len(hist) == 0:
                new_hist = pd.DataFrame(add)
            elif type(add) is not dict:
                # assumes its already a dataframe (like from pd.json_normalize())
                new_hist = pd.concat((hist, add), ignore_index=True)
            else:
                new_hist = pd.concat((hist, pd.DataFrame(add, index=[0])), ignore_index=True)

            hist = new_hist.copy()
            #print("HISTORY ADD", pd.DataFrame(add, index=[0]))
            #print("NEW HIST SHAPE", new_hist.shape)

        # by now, hist should not be empty
        assert len(hist) != 0

        # get single scores: series -> Really the results of single rounds, not entire player averages
        #id_sep = "(<><)"
        #hist["id"] = hist["name"] + id_sep + hist["team"] # fish :)
        #singles = hist.groupby("id")["score"].mean().sort_values(ascending=False, ignore_index=True) # this would average every players round scores

        #print("HIST")
        #print(hist.columns)
        #print("HIST HEAD")
        #print(hist.head())

        #print("get_semester", get_semester)
        if get_semester is not None:
            hist = hist[hist["semester"].astype(str) == str(get_semester)]
        #print("HIST HEAD")
        #print(hist.head())
        
        singles = hist.sort_values("score", ascending=False, ignore_index=True)#.set_index("id")
        singlesTop3 = singles.iloc[:3]

        # get team scores: series
        teams = hist.groupby("team")["score"].mean().sort_values(ascending=False, ignore_index=True)
        teamsTop3 = teams.iloc[:3]

        if add is not None: # if there is something new added to the history, actually save the file
            self.save_history(new_hist)

        # lambdas to split up the dicts into lists
        to_list = lambda x: [[int(v), k] for k, v in x.items()] # score, team
        if "semester" in singles.columns:
            from_df = lambda x: [[v["player"], v["team"], v["score"], v["semester"], v["attestation"]] for i, v in x.iterrows()] # score, player, team
            columns = ["Player", "Team", "Score", "Semester", "Attestation"]
        else:
            from_df = lambda x: [[v["player"], v["team"], v["score"]] for i, v in x.iterrows()] # score, player, team
            columns = ["Player", "Team", "Score"]

        #to_list_split = lambda x: [[v, k.split(id_sep)[0], k.split(id_sep)[1]] for k, v in x.items()] # score, player, team        

        out = { # podium is not used at the moment
            "single_table": from_df(singles),
            "single_columns": columns,
            #"single_podium": from_df(singlesTop3),
            "team_table": to_list(teams.to_dict()),
            #"team_podium": to_list(teamsTop3.to_dict()),
        }
        if add is not None: # provide the index of the added history item 
            index = singles.index[(singles["player"] == add["player"]) & (singles["team"] == add["team"]) & (singles["score"] == add["score"])]
            out["single_new_index"] = index.tolist()[0]

        return out

    def build_HTML(self):
        """ Based on self.TREE, build the input fields for this gamemode flow. Returns the HTML content inside of the fieldset container as well as the name of the gamemode """
        border = "<hr>" # horizontal line

        steps = []
        for k, v in self.TREE.items():
            inputs = v[3]
            button_name = inputs[0]

            html = ""
            if button_name is not None:
                ID = "-".join([self.gamemode_name, k, "submit"])
                html = f"<input type='checkbox' id='{ID}' class='submit-step'><label for='{ID}' data-og='{button_name}'>{button_name}</label>"

            for specials in inputs[1:]:
                ID = "-".join([self.gamemode_name, k, specials["name"]])
                typ = specials["type"]
                placeholder = specials["placeholder"]
                key = specials["name"]

                other = ""
                #if "value" in specials.keys():
                #    other = f"value='{specials['value']}'"
                print(specials)
                for k2, v2 in specials.items(): # dont iterate over k,v (already used above)
                    other += f" {k2}='{v2}'"

                html += f"<input type='{typ}' id='{ID}' name='{key}' placeholder='{placeholder}' {other}>" # TODO: how to reset on reset command?

            div_id = "-".join([self.gamemode_name, k])
            html = f"<div class='button-list step' id='{div_id}'>" + html + "</div>"

            steps.append(html)

        #print(steps)
        return border.join(steps), self.gamemode_name


    #%% Common ball interactions

    def check_starting_positions(self, inp, starting_positions=[], tolerance=50, update_gameimage=None):
        """ Checks if the ball(s) is/are placed on the starting point(s). Returns True if it is correct, False if not. Local returns contains "gameimage-updates" with balls to signal misplacements. Forward returns contains the message what is wrong or correct. See common_utils.check_positions for more details. For starting positions determined after init, use a (lambda) function to provide the starting coords.
        
        Args:
            inp (dict): input from the client, must contain key "coordinates"
            starting_positions (dict|list|function): the positions of the balls at the start. For syntax see common_utils.check_positions. 
            tolerance (int): max radial distance a ball can have from a position before it is determined misplaced
            update_gameimage (GameImage): if set, also updates the passed GameImage objects definition (call by reference) according to the local_returns["gameimage-updates]. Only updates the text field. Useful when the GameImage displayed is set in self.TREE as self.gameimage.definition.

        Returns:
            within_tolerance (bool): True if all balls are placed correctly, False otherwise
            local_returns (dict): special stuff to handle on the server. Mostly contains "gameimage-updates": [{},...] to update the gameimage
            forward_returns (dict): message that gets send to the client

        """
        
        if callable(starting_positions):
            starts = starting_positions()
        else:
            starts = starting_positions.copy()

        coords = inp["coordinates"]
        within_tolerance, message, signal_coords = check_positions(inp["coordinates"], starts, tolerance=tolerance)

        local_returns = {"gameimage-updates": [{"type": "balls", "coords": signal_coords}, {"type": "text", "text": f"{self.gamemode_name}: {message}"}]}
        if not within_tolerance:
            local_returns["sound"] = "please_correct_ball_positions"
        else:
            local_returns["sound"] = "finished"
            local_returns["gameimage-updates"][1]["text"] = self.gamemode_name + ": Now play"
        
        if not update_gameimage is None:
            update_gameimage.update_definition(local_returns["gameimage-updates"][1])

        return within_tolerance, local_returns, {"message": message} 

