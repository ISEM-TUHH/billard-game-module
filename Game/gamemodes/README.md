# Gamemodes of the game module
This directory collects all gamemodes.

Each gamemode is designed as a python class with a `dict` defining the API endpoints needed for operation (called `api_dict`). Gamemodes need to be registered with the main game module (`Game/__init__.py`).