from .kp2 import KP2

class FinalCompetition(KP2):
    """ This is an abstraction of the KP2 mode. It essentially is the same, only using a different number of challenges and allows for the input of previously collected bonus points. It is used in the final competition of the KP2/MDP2 project.

    """
    def __init__(self):
        self.__file__ = __file__

        occurences = {
            "precision": 3,
            "distance": 3,
            "break": 1,
            "longest_break": 3
        }

        KP2.__init__(self, occurences=occurences, gm_name="Final Competition") # super init

        self.WEBSITE_TEMPLATE = "kp2.html"

        self.img_definition = [ # TODO: outsource to config file?
            {
                "type": "text",
                "text": "Welcome to the final competition! Select a gamemode"
            },
            {
                "type": "central_image",
                "img": "isem-logo-big"
            }
        ]
        self.gameimage.draw_from_dict(self.img_definition)
