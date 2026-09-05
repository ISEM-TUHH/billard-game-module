# Game Module - Billard@ISEM

The repository provides the game module for the Billard@ISEM system.

## Installation
These steps must be done for both local and docker installations. We recommend the docker installation.
+ Clone the repository: `git clone https://github.com/ISEM-TUHH/billard-game-module.git`
+ Modify `config.json` and/or `test_config.json` to find your other modules as well as add a `.env` file as specified later on
+ Download the font used for generating images for the beamer and paste it into the `fonts` folder. 
    - We use `Minecraft-Regular.otf` from publicly available Minecraft font collections.

### Docker container
This is the recommended way to run this module, as it uses a MongoDB server too. It is possible to install locally, but you'd need to get the MongoDB server running too (and maybe change the preconfigured address of it + user authentication).
```bash
docker compose --profile build build
```
- Run production server: `docker compose --profile prod up`
- Run development server: `docker compose --profile dev up`
- Stop with `docker compose --profile [profile] down`
- If you choose another network port than `5000`, this must also be modified in the `compose.yaml`

> [!IMPORTANT]
> A lot of functionalities require the other modules to also be up and running (mostly Game, Camera and Beamer modules). See https://github.com/ISEM-TUHH for the respective modules.

![The website of the KP2 gamemode with the Longest Break challenge selected](https://github.com/ISEM-TUHH/billard-game-module/blob/main/docs/source/images/website.png?raw=true)
*The website of the KP2 gamemode with the Longest Break challenge selected*

### .env fields
The following fields are needed to be set in a `.env` file in the root directory:
```bash
# DOWNLOAD SECTION: authentication for /download
USER=XXX
PASSWORD=XXX

# TABLE: authentication for the table to communicate with the global API (for online games)
TID=XXX
TAUTH=XXX

# API: connection details for the global API
ADDRESS=https://XXX.XXX.XXX.XXX
PORT=XXX

# Password to change the configuration of gamemodes in the browser
CONFIG_PASSWORD=XXX

# AUTH MONGODB: to be used from MongoDB Compass to login into the database
MONGO_INITDB_ROOT_USERNAME=admin (this is just a suggestion)
MONGO_INITDB_ROOT_PASSWORD=XXX
```
To be able to communicate with the global API to play online games you need to be registered with us. Write us an e-mail if you want to get registered. We will provide you with a `TID` and `TAUTH`

Important: The API is not publicly available yet, we are working on it.

## Documentation
Documentation is generated using sphinx. A prebuilt PDF can be found in `docs/latex`.
To generate the documentation, use 
```bash
make html
```
in the `docs` directory for a `html` output or `make latexpdf` for a PDF. This requires an installation of LaTeX on the system.