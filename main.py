from Game import Game
from dotenv import load_dotenv

if __name__ == "__main__":

	print("Starting game module...")
	g = Game()
	
	if g.TEST_MODE:
		load_dotenv("dev2.env")
	else:
		load_dotenv()

	g.app_run()