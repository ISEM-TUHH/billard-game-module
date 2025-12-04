""" This file initializes the gamemodes """
# Single gamemodes
from .distance import Distance
from .precision import Precision
from .single_break import Break
from .longest_break import LongestBreak

from .dummy import Dummy

# Meta gamemodes
from .kp2 import KP2

from .online_game import OnlineGame
from .local_game import LocalGame