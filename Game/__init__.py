from .billard_base_module.Module import Module
from .billard_base_module.RemoteModules import Camera, Beamer

# imports for sphinx to find
from . import GameImage, GameEngine, GameRules, Player, billard_base_module



#from .GameImage import GameImage, BilliardBall
#from .Elo import Elo
import numpy as np
import pandas as pd
import os
from pathlib import Path
from flask import Flask, jsonify, render_template, request, redirect, session, Response
import socket
#import urllib.request
import requests
import json
import cv2
import time
import logging
import dotenv

from PIL import Image

from .gamemodes import KP2, Precision, Distance, Break, LongestBreak, Dummy, online_game, local_game, FinalCompetition # OnlineGame, local_game#LocalGame

class Game(Module):
	"""Implements central game scheduling functions

	Bundles all modules APIs and provides the central website.

	In a default environment, this module runs in test mode (specified in parent class billard_base_module.Module). To start in production mode, set the environment variable `PROD_OR_TEST=PROD`.

	Attributes:
		base_image (list): Supplies the definition for a default GameImage that gets displayed when the game website is opened, but no gamemode is selected.
		current_dir (str): Absolute path of this file.
		storage (str): concat of current_dir and storage_folder (absolute path)
		camera (Camera): interface object to the remote camera module, configured from passed config
		beamer (Beamer): like camera, but for the beamer module.
		gameimage (GameImage): the current displayed image. Most of the times this gets pushed to the beamer module.
		GAMEMODES (dict): mapping gamemode names to GameMode objects. Gets used to pipe input from the client website (posted on `gamemodecontroller` endpoint) to the gamemode specified in the posted data.
		api (dict): nested dictionary of all API endpoints. 
	"""

	#supermode = "base" # current gamemode. base: on booting up, before selecting mode. play-local: normal game local. play-online: online game with another billiard robot somewhere else. kp2: mode of selecting kp2 testat, with kp2-t1...t3 being the different testate.
	#current_players = [] # will store the player objects
	#winner = {} # player object that last won the game		
	
	base_image = [
				{
					"type": "text",
					"text": "Billard@ISEM"#"Billard@ISEM"
				},
				{
					"type": "central_image",
					"img": "isem-logo-big"
				},
			]
	
	
	def __init__(self, config="config/config.json", test_config="config/test_config.json", storage_folder="storage", download_folder="gamemodes/resources", template_folder="templates"):
		"""Initializes the Game object. Provide relative paths (to this file).

		:param config: path to a configuration `.json` to be used in production mode
		:type config: str, optional
		:param test_config: path to a configuration `.json` to be used in test mode
		:type test_config: str, optional
		:param storage_folder: path to a folder where some storage files are kept. Not really relevant, only players.json gets read from there.
		:type storage_folder: str, optional
		:param download_folder: relative path to a folder where resources that should be available to download from endpoint `/download` after authentication
		:type download_folder: str, optional
		:param template_folder: path to the folder containing the jinja2 templates.
		:type template_folder: str, optional
		"""

		current_dir = os.path.dirname(__file__)
		self.current_dir = current_dir
		self.storage = os.path.join(current_dir, storage_folder)
		self.download_dir = os.path.join(current_dir, download_folder)

		Module.__init__(self, config=f"{current_dir}/{config}", test_config=os.path.join(current_dir, test_config), template_folder=f"{current_dir}/{template_folder}", storage_folder=self.download_dir, static_folder=f"{current_dir}/static")

		self.camera = Camera(self.getModuleConfig("camera"))
		self.beamer = Beamer(self.getModuleConfig("beamer"))

		self.gameimage = GameImage.GameImage(definition=self.base_image.copy())
		self.beamer.push_image(self.gameimage.getImageCV2())

		with open(f"{self.storage}/players.json") as f:
			self.players = json.load(f)

		api_secrets = {k: v for k,v in self.secrets.items() if k in ["TID", "TAUTH", "ADDRESS", "PORT"]} 
		
		self.GAMEMODES = {
			"kp2": KP2(),
			"final_competition": FinalCompetition(),
			"online_game": online_game.OnlineGame(api_secrets),
			"local_game": local_game.LocalGame(api_secrets)
		}


		socket_dict = {
			"gamemode-socket": self.gamemode_socket_handler
		}
		#self.add_all_sockets(socket_dict)

		api_dict = { # sorted by functionality group
			"": self.index,
			"general": {
				"ballimagenumber": self.get_ball_image,
				"correctedcoords": self.beamer_correct_coords,
				"beameroff": self.beamer_off,
				"takeimage": self.take_image,
				"settext": self.beamer_update_manual_text
			},
			"camera": {
				"coords": self.forward_coords
			},
			"gamemodecontroller": self.gamemode_controller,
			"gamemode/<mode>": self.get_gamemode_website,
			"view_csv/<file>": self.view_csv
		}

		self.add_all_api(api_dict)
		return


	# META BASIC INTERACTION ########################################################

	def render_template_camera(self, file, **kwargs):
		""" Oftentimes we need to render a website that contains the camera livestream. We dont want to write it statically nor do we want to pass it everytime """
		return render_template(file, camera_address_video_feed=self.camera.endpoint("/website/video_feed"), camera_address=self.camera.address, **kwargs)

	def index(self):
		"""Renders and returns the index.html website (gamemode selection)
		"""
		print(f"Client connected.")
		# show all available gamemodes on the website
		#available = self.list_available_gamemodes()

		# TODO: dynamically generate the funnel?
		#self.supermode = "base"
		#self.beamer_make_gameimage()
		return render_template('index.html', camera=self.camera.address, beamer=self.beamer.address)

	def get_ball_image(self):
		"""Get the image of a certain ball by number.

		Send the number/name of the ball as request argument (`/ballimagenumber?n=4`)

		Todo:
			- change endpoint to template like `/ballimage/<number>` instead of current system with args.
		"""
		n = int(request.args.get("n"))
		ball = GameImage.BilliardBall(n)
		img = np.array(ball.getImg(60))[:,:,[2,1,0]] # 60x60 pixels, transformed to a cv2 object type

		#print(n)
		_, buffer = cv2.imencode(".png", img)
		return Response(buffer.tobytes(), mimetype="image/png")

	def view_csv(self, file):
		""" Renders a single csv file as a html table and shows it. CSV files must not have an index and must be separated by tabs (\t). If the file does not exist or does not end in `.csv`, returns status 404 or 403 """
		fileStorage = os.path.join(self.storage_dir, file)
		fileResources = os.path.join(self.current_dir, "gamemodes", "resources", file)
		if not file.endswith(".csv"):
			return "", 403
		elif Path(fileStorage).exists():
			path = fileStorage
		elif Path(fileResources).exists():
			path = fileResources
		else:
			return "", 404
		html = pd.read_csv(path, sep="\t", index_col=False).to_html()
		return html

	def take_image(self):
		""" Turn of the beamer and take an image.
		"""
		self.beamer.off()
		time.sleep(0.1)
		res = self.camera.save_image()
		print(res)
		self.beamer.push_image(self.gameimage.getImageCV2())
		
		return res

	# INTERACTIONS WITH CAMERA MODULE ###############################################
	from ._camera_interface import forward_coords, camera_save_image

	# INTERACTIONS WITH BEAMER MODULE ###############################################
	from ._beamer_interface import beamer_push_image, beamer_off, beamer_make_gameimage, beamer_correct_coords, beamer_update_manual_text

	# INTERACTIONS FOR NORMAL GAME ##################################################
	#from ._game_local import get_site_game_local, game_local_enter_round, game_local_start_round, game_determine_start
	# INTERACTION FOR ONLINE GAME ###################################################
	#from ._game_online import get_site_game_online, online_start_game, get_site_register_player

	# INTERACTIONS FOR EXAM MODE ####################################################
	#from ._kp2 import get_site_kp2, enter_round_kp2, select_mode_kp2, kp2_set_precision_difficulty, kp2_get_live_value, kp2_calc_score, kp2_update_score_data_base # import all methods from _kp2.py
	#from ._lat import get_site_lat, enter_round_lat # import all methods from _lat.py

	# INTERACTION FOR TRICKSHOT MODE ################################################
	#from ._trickshots import load_trickshot, list_trickshots, get_site_trickshots, get_site_create_trickshots


	# GAMEMODE CONTROLLER ###########################################################
	from ._gamemode_controller import gamemode_controller, get_gamemode_website, list_available_gamemodes, gamemode_socket_handler

	# INTERNAL FUNCTIONS ############################################################

	def save_players(self):
		"""Writes the current self.players list to players.json
		"""
		parsed = json.dumps(self.players, indent=4)
		with open(f"{self.storage}/players.json", "w") as f:
			f.write(parsed)
		
		
		

if __name__ == "__main__":
	g = Game()
	#g.add_website("index.html")
	g.app.run(host="0.0.0.0")