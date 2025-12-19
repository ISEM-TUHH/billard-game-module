# Gamemodes of the game module
This module collects all gamemodes.

Each gamemode is designed as a python class with a `dict` defining the game flow called `GameMode.TREE`. An example for the `TREE` is copied from distance.Distance:
```python
self.TREE = {
    "init": [
        lambda inp: self.check_starting_positions(inp, starting_positions=[self.starting_point_raw]), # function to call on input: self.check_starting_points is provided by the parent class GameMode. A lambda expression is used to unify the input to only take in one argument.
        {"True": "strike", "False": "init"}, # based on the output, what should state should be assumed next?
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
```
The input `inp` that is piped into  is a standardized `dict` send by the client, consisting of at least the fields
```python
inp = {
    "gmode": "distance", # name of the gamemode this input should be passed to (names as set as keys in Game.GAMEMODES)
    "action": "game", # action for what this input should be used for:
        # game: pass it to the normal GameMode.entrance function, will normally get passed to the specified function in GameMode.TREE[GameMode.state][0]
        # settings: pass it to the GameMode.settings function (this is specified/decided in GameMode.entrance)
        # show: pass it to the GameMode.show function, which returns a current GameImage object without modifying anything of the GameMode (this is specified in Game.gamemode_controller)
    # all other fields are specific to the gamemode selected
}
```
The client website sends this `json`-data to the API endpoint `/gamemodecontroller` of the Game module. For testing, this can also be done by API testing systems like postman or a simple `curl` request.


Gamemodes need to be registered with the main game module (`Game/__init__.py`)