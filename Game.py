from Module import Module
from Elo import Elo
import numpy as numpy
import pandas as pd
import os
from flask import Flask, jsonify, render_template, request, redirect, session
import socket
#import urllib.request
import requests
import json

class Game(Module):
	"""Implements central game scheduling functions

	Bundles all modules APIs and provides the central website.
	"""
	
	mode = "base" # current gamemode. base: on booting up, before selecting mode. play-local: normal game local. play-online: online game with another billiard robot somewhere else. kp2: mode of selecting kp2 testat, with kp2-t1...t3 being the different testate.
	current_players = [] # will store the player objects
	winner = {} # player object that last won the game
	
	def __init__(self, config="config/config.json", storage_folder="storage", template_folder="templates"):
		Module.__init__(self, config=config, template_folder=template_folder)

		self.storage = storage_folder
		with open(f"{self.storage}/players.json") as f:
			self.players = json.load(f)

		api_dict = {
			"": self.index,
			"v1": {
				"getlocalplayers": self.get_local_players,
				"updateelo": self.do_update_elo
			},
			"sites": {
				"kp2": self.get_site_kp2,
				"lat": self.get_site_lat
			}
		}

		self.add_all_api(api_dict)
		return


	# META BASIC INTERACTION ########################################################

	def index(self):
		print(f"Client connected.")
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


	# INTERACTIONS FOR NORMAL GAME ##################################################

	# INTERACTIONS FOR EXAM MODE ####################################################
	def get_site_kp2(self):
		if request.method == "POST":
			return render_template("kp2.html")

	from ._lat import get_site_lat # import all methods from _lat.py

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
	g.app.run()