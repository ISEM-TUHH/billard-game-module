from .billard_base_module.Module import Module

from .GameImage import GameImage, BilliardBall
from .Elo import Elo
import numpy as np
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session, Response
import socket
#import urllib.request
import requests
import json
import cv2
import time
import logging

class Game(Module):
	"""Implements central game scheduling functions

	Bundles all modules APIs and provides the central website.
	"""
	
	supermode = "base" # current gamemode. base: on booting up, before selecting mode. play-local: normal game local. play-online: online game with another billiard robot somewhere else. kp2: mode of selecting kp2 testat, with kp2-t1...t3 being the different testate.
	current_players = [] # will store the player objects
	winner = {} # player object that last won the game
	
	def __init__(self, config="config/config.json", storage_folder="storage", template_folder="templates"):
		current_dir = os.path.dirname(__file__)
		self.current_dir = current_dir
		self.storage = current_dir + "/" + storage_folder

		Module.__init__(self, config=f"{current_dir}/{config}", template_folder=f"{current_dir}/{template_folder}", storage_folder=self.storage)

		# disable logging every request, as there are a lot of requests
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)

		with open(f"{self.storage}/players.json") as f:
			self.players = json.load(f)

		api_dict = { # sorted by functionality group -> lat, kp2, game-online, game-local, trickshots etc
			"": self.index,
			"selector": { # for the selection progress
				"getlocalplayers": self.get_local_players,
			},
			"sites": {
				"kp2": self.get_site_kp2,
				"lat": self.get_site_lat,
				"trickshots": self.get_site_trickshots,
				"gamelocal": self.get_site_game_local,
				"gameonline": self.get_site_game_online,
				"register_new": self.get_site_register_player
			},
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
			"lat": {
				"enterround": self.enter_round_lat
			},
			"kp2": {
				"enterround": self.enter_round_kp2,
				"selectmode": self.select_mode_kp2,
				"cosmetics": {
					"precdif": self.kp2_set_precision_difficulty,
					"value": self.kp2_get_live_value
				},
				"config": {
					"updatescores": self.kp2_update_score_data_base
				}
			},
			"game": {
				"updateelo": self.do_update_elo,
				"startgame": self.game_local_start_round,
				"enterround": self.game_local_enter_round,
				"determinestart": self.game_determine_start
			},
			"online": {
				"startgame": self.online_start_game
			},
			"trickshots": {
				"list": self.list_trickshots,
				"load": self.load_trickshot,
				"sitecreate": self.get_site_create_trickshots
			}
		}

		self.add_all_api(api_dict)
		return


	# META BASIC INTERACTION ########################################################

	def index(self):
		print(f"Client connected.")
		self.supermode = "base"
		self.beamer_make_gameimage()
		return render_template('index.html')


	def get_local_players(self):
		""" Returns all names + team from players.json
		"""
		pastestr = [f"{x['name']}, {x['team']}" for x in self.players]
		#print(pastestr)
		return jsonify(pastestr)

	def do_update_elo(self):
		""" Updates the elo rating in the local players dict and return the updated current players
		"""
		if len(self.current_players) != 2:
			em = f"Trying to update elo of no players, current players are: {self.current_players}"
			print(em)
			return em
		elif self.winner == None: # If no one has won yet
			em = f"Trying to update elo but there is no winner"
			print(em)
			return em
		
		turnout = 0.5 if self.winner==0.5 else self.current_players.index(self.winner)

		elo = Elo()
		updatedCurrentPlayers = elo.match(self.current_players, turnout)
		for p in updatedCurrentPlayers: # update main list of players
			for o in self.players:
				if p["id"] == o["id"]:
					o["elo"] = p["elo"]
		
		self.winner = None # reset the winner to prevent double writing to elo from one match
		self.save_players() # write updated list to players.json

	def get_ball_image(self):
		""" Get the image of a certain ball by number.
		"""
		n = int(request.args.get("n"))
		ball = BilliardBall(n)
		img = np.array(ball.getImg(60))[:,:,[2,1,0]] # 60x60 pixels, transformed to a cv2 object type

		#print(n)
		_, buffer = cv2.imencode(".png", img)
		return Response(buffer.tobytes(), mimetype="image/png")

	def take_image(self):
		""" Turn of the beamer and take an image.
		"""
		self.beamer_off()
		time.sleep(1.5)
		res = self.camera_save_image()
		print(res)
		return res

	# INTERACTIONS WITH CAMERA MODULE ###############################################
	from ._camera_interface import forward_coords, camera_save_image

	# INTERACTIONS WITH BEAMER MODULE ###############################################
	from ._beamer_interface import beamer_push_image, beamer_off, beamer_make_gameimage, beamer_correct_coords, beamer_update_manual_text

	# INTERACTIONS FOR NORMAL GAME ##################################################
	from ._game_local import get_site_game_local, game_local_enter_round, game_local_start_round, game_determine_start
	# INTERACTION FOR ONLINE GAME
	from ._game_online import get_site_game_online, online_start_game, get_site_register_player

	# INTERACTIONS FOR EXAM MODE ####################################################
	from ._kp2 import get_site_kp2, enter_round_kp2, select_mode_kp2, kp2_set_precision_difficulty, kp2_get_live_value, kp2_calc_score, kp2_update_score_data_base # import all methods from _kp2.py
	from ._lat import get_site_lat, enter_round_lat # import all methods from _lat.py

	# INTERACTION FOR TRICKSHOT MODE ################################################
	from ._trickshots import load_trickshot, list_trickshots, get_site_trickshots, get_site_create_trickshots

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