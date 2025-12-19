from pathlib import Path
import pandas as pd
import json
from ..GameImage import GameImage
from .common_utils import *

class GameMode:
    """ The parent class to all gamemodes. Provides common implementations like show and history management 

    Attributes:
        state (str): the current state of the GameMode. Usually starts with `init` and ends with `finished`, after which it resets.
        TREE (dict): mapping of the current state to actions that should be taken when the next user input arrives. The example below is from a Distance object:
            
            .. code:: python3

                self.TREE = {
                    "init": [
                        lambda inp: self.check_starting_positions(inp, starting_positions=[self.starting_point_raw]), # function to call on input: self.check_starting_points is provided by the parent class GameMode. A lambda expression is used to unify the input to only take in one argument.
                        {"True": "strike", "False": "init"}, # based on the output of the previous function, what should state should be assumed next?
                        lambda: [   
                            # GameImage.definition that should be shown when this is the state. As lambda expression to be evaluated on call (dynamically change values from self.[attribute] like self.starting_point). See GameImage documentation for details.
                            {
                                "type": "text",
                                "text": "Distance Challenge: Place the ball on the starting point",
                                "subimg": "isem-logo"
                            },
                            {
                                "type": "balls", # starting point
                                "coords": self.starting_point,
                                "ref": "balls-base" # manually set the reference so it does not get overwritten when displaying other balls
                            }
                        ],
                        ["Start"] # describe name of button and special inputs that should be shown on the client. Gamemodes that are parts of the KP2 gamemode (KP2.GAMEMODES) have their inputs be dynamically generated based on this field. See GameMode.build_HTML for more information.
                    ],
                    "strike": [
                        self.calculate_score, # 
                        {"True": "finished"}, # no other outputs possible
                        lambda: [ # as soon as the state (self.state) is "strike", this gets assigned to Game.gameimage and displayed on the beamer
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
                            "type": "number", # input fields are required to be changed at least once for the main button (here: Measure) to become selectable. `types` are just html input types.
                            "name": "collisions", # generates a number input field which will be available in inp["collisions"]
                            "placeholder": "Collisions", # IDs of input get set to [self.gamemode_name]-[state/step (here `strike`)]-[name]
                        }]
                    ],
                    # a "finished" action is automatically added by the parent class GameMode if not already specified.
                }

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
        """This is the central function of every gamemode (can be overloaded). This method is called by Game.gamemode_controller, which also handles the return values. 

        In normal gamemodes (which do not overload this), the action is determined by the structure of GameMode.TREE

        Args:
            inp (dict): json data input from the client. Usually posted to the endpoint `/gamemodecontroller`.

        Returns:
            dict, GameImage, (str | None): the output that gets send to the client as a response (must contain the fields "signal", which is usually the current/new self.state value). The returned GameImage object is the new image that should get shown as a response to the request. The final string is the name of a sound file (just the file name, without path or ending) on the Beamer module that should get played (if it is None, nothing will get played).
        """
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
        """ Currently not in use. Using self.SOCKETS handle the socket event. Pipes the input into the function registered in self.SOCKETS[self.state]. """
        if hasattr(self, "SOCKETS") and self.state in self.SOCKETS.keys():
            self.SOCKETS[self.state](json_data)


    def show(self, inp={}):
        """When (re)entering the gamemode, determine what gameimage to show.
        
        If the gamemode contains children gamemodes, they must be organized in a dictionary named self.GAMEMODES with the key self.SUBSELECTOR in the input inp selecting the child gamemode by key of the dictionary. 

        Returns:
            GameImage: a copy of the GameImage object of this GameMode object or a child 
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
        """Reset the gamemode object but keep changes made to the settings. If reset inplace, overwrites itself without returning itself. With inplace=True, it returns valid values useful for usage as `lambda inp: self.reset(inplace=True)` in GameMode.TREE, as used in e.g. the default `finished` step from GameMode.__init__.

        Returns:
            GameMode or (bool, dict, dict): the reinitialized gamemode OR (False, {}, {}) as "neutral" output for calls in GameMode.entrance (if inplace=True)
        """
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
        """Gets the history table from self.history_file. If the file does not exist, returns an empty dataframe

        Returns:
            pd.DataFrame: history or empty dataframe
        """
        if self.history_file.exists():
            hist = pd.read_csv(self.history_file, sep="\t", index_col=False)
        else:
            hist = pd.DataFrame()
        return hist

    def save_history(self, history):
        """Writes a passed dataframe to self.history_file (tab-separated, without an index)

        Args:
            history (pd.DataFrame): The dataframe to get saved. Usually contains the history of all rounds of the specific gamemode, with nested data being normalized (see pd.json_normalize)
        """
        history.to_csv(self.history_file, sep="\t", index=False)

    def save_json_history(self, history):
        """Appends a passed dict to a list of dicts in self.json_history_file.

        Args:
            history (dict): arbitrary dictionary, usually a dump of all information of the current round. 
        """
        entire_history = []
        with open(self.json_history_file, "r") as file:
            entire_history = json.load(file)
        entire_history.append(history)
        with open(self.json_history_file, "w") as file:
            json.dump(entire_history, file, ensure_ascii=False, indent=4)

    def history(self, history=None, add=None, get_semester=None):
        """ Get the player/team rankings.
        
        Returns a dictionary that can be used to generate html code for showing the list and podium. History files are organized inside the `resources` directory, always starting with the stem of the gamemode filename (kp2.py -> `kp2_. . .`). History file must be name [gamemode]_history.csv.
        If adding to the history, set add to a dictionary containing all fields you want to save (must contain `player`, `team` and `score`). A timestamp automatically gets added.

        When a new entry was added, the history gets saved.

        See Game/static/history_handler.js or Game/templates/base.html for the usage of this output in JavaScript or jinja2 templates.

        Args:
            history (pd.DataFrame | None): A table containin a history entry in each row. It must at least contain the columns `player`, `team` and `score`. If it is None, the table gets loaded from the `.csv` (tsv) path specified in `GameMode.history_file`. If this file does not exist (yet), creates an empty pd.DataFrame.
            add (pd.DataFrame | json | None): A history entry with the same field as the history should have to get added to the history. If it is unset (None), nothing gets added. If it is set, the returned dict has a field `single_new_index` of the row number where the new entry has been inserted (in the returned sorted table, in the saved table it will be appended at the end).
            get_semester (int | str | None): If set (not None), the returned tables will only contain entries with the same value in the `semester` column. Requires the `semester` column to exist, as in the KP2 mode.

        Returns:
            dict: a dictionary with the fields `single_table` (list of lists with `player`, `team`, `score` in each row, if existing also `semester` and `attestation`), `single_columns` (list of the name of the columns in `single_table`), `team_table` (list of lists always containing the `team` and `score`, which is averaged across all members of the team.). All tables are sorted with the highest score on top. If a new entry was added, the field `single_new_index` (int) also exists with the index of the new entry in the sorted `single_table`

        Todo:
            - Check if the line `assert len(hist) != 0` is really needed? How can we automatically setup new gamemodes histories?
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

        #print(teams)

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
        """ Based on self.TREE, build the input fields for this gamemode flow. Returns the HTML content inside of the fieldset container as well as the name of the gamemode 
        
        Inputs that get rendered are defined by the fourth (starting at 0: 3rd) entry in a self.TREE value field. An example is
        
        .. code:: python3

            ["Measure", #IDs of this button gets set to [self.gamemode_name]-[state/step (here `strike`)]-submit
                { # special input fields needed in this step: 
                "type": "number", # input fields are required to be changed at least once for the main button (here: Measure) to become selectable. `types` are just html input types.
                "name": "collisions", # generates a number input field which will be available in inp["collisions"]
                "placeholder": "Collisions", # IDs of input get set to [self.gamemode_name]-[state/step (here `strike`)]-[name]
            }]

        #. The first field "Measure" defines a checkbox with the text "Measure". Clicking on it starts the interaction flow to get/update the coordinates. If this field is `None`, there will be no checkbox displayed.
        #. The second field defines an arbitrary html input element. All key-value pairs should be valid attributes of a html input element (see https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input).
            #. There can be an arbitrary amount of special input fields like this
        #. Input buttons and checkboxes trigger a js-event to collect the inputs of all other specified inputs in this step/state and send their value as [name]: [value] pairs in a json-object to the specified gamemode's entrance method. The [value] of checkbox inputs gets translated to true/false.

        Returns:
            str, str: html-code of all steps joined with `<hr>` and the name of the gamemode (self.gamemode_name) 

        """
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
                specials["id"] = "-".join([self.gamemode_name, k, specials["name"]])
                #typ = specials["type"]
                #placeholder = specials["placeholder"]
                #key = specials["name"]

                other = ""
                #if "value" in specials.keys():
                #    other = f"value='{specials['value']}'"
                #print(specials)
                for k2, v2 in specials.items(): # dont iterate over k,v (already used above)
                    other += f" {k2}='{v2}'"
                html += f"<input{other}>" # TODO: how to reset on reset command?

                #html += f"<input type='{typ}' id='{ID}' name='{key}' placeholder='{placeholder}' {other}>" # TODO: how to reset on reset command?

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
            tolerance (int): max radial distance a ball can have from a position before it is determined misplaced. Given in the same scale as the coordinates, which usually are mm (1px = 1mm).
            update_gameimage (GameImage): if set, also updates the passed GameImage objects definition (call by reference) according to the local_returns["gameimage-updates]. Only updates the text field. Useful when the GameImage displayed is set in self.TREE as self.gameimage.definition.

        Returns:
            bool, dict, dict: within_tolerance: True if all balls are placed correctly, False otherwise || local_returns: special stuff to handle on the server. Mostly contains "gameimage-updates": [{},...] to update the gameimage | forward_returns: message that gets send to the client

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

