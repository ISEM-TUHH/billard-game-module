from Game import Game

if __name__ == "__main__":
	g = Game()
	#g.add_website("index.html")
	g.app.run(host="0.0.0.0", port="5001")