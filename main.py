from Game import Game

if __name__ == "__main__":

	g = Game()
	#g.add_website("index.html")
	#g.app.run(host="0.0.0.0", port="5000")
	# use Module.app_run() to use the host and port given by config files (test or prod) as well as debug mode.
	g.app_run()