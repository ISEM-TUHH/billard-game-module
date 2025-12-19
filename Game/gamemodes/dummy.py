from ..GameImage import GameImage
from .GameMode import GameMode

class Dummy(GameMode):
    """ This gamemode only serves as a dummy mode to test the system """
    def __init__(self):
        self.__file__ = __file__
        GameMode.__init__(self)
        
        print("A dummy object was created")
        self.gameimage = GameImage()
        self.gameimage.draw_from_dict([
            {
                "type": "text",
                "text": "Hello from the dummy gamemode!"
            }
        ])


    def entrance(self, inp):
        print("dummy.entrance() called")
        print("input:", inp.keys(), "\n", inp)

        return {"signal": "forward", "score": 100}, self.gameimage.copy()