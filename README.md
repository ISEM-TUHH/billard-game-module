# Game Module - Billard@ISEM

The repository provides the game module for the Billard@ISEM system.

## Installation
+ Clone the repository: `git clone https://github.com/ISEM-TUHH/billard-game-module.git`
+ Modify `config.json` and/or `test_config.json` as well as add a `.env` file as specified later on
+ From inside the repository folder create and install all relevant python dependencies: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
+ Download the font used for generating images for the beamer and paste it into the `fonts` folder. 
    - We use `Minecraft-Regular.otf` from publicly available Minecraft font collections.
+ For testing the system, run `python main.py`.
    + This starts the server using the configuration from `test_config.json`
    + Open the specified webpage and check that everything works
+ To run in the goal environment, set the environment variable `PROD_OR_TEST` (`export PROD_OR_TEST=PROD`) and restart the server
    + Now the configuration from `config.json` is used
+ Add a systemd service so the server automatically runs when the device boots up
    + See the exemplary `job.service` file (you can change the name, exemplary name)
    + Move the `job.service` into `/etc/systemd/system/` (most likely a `sudo` operation)
    + Reload the daemon, enable and start the service: `sudo systemctl reload-daemon && systemctl enable job.service && systemctl start job.service`
    + Check if the server is running as intended: `sudo journalctl -u job.service`
    + If succesfully started, the server should now be accessible under the address/port provided in `config.json`.
+ A lot of functionalities require the other modules to also be up and running (mostly Game, Camera and Beamer modules). See https://github.com/ISEM-TUHH for the respective modules.

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
```
To be able to communicate with the global API to play online games you need to be registered with us. Write us an e-mail if you want to get registered. We will provide you with a `TID` and `TAUTH`

Important: The API is not publicly available yet, we are working on it.

## Documentation
Documentation is generated using sphinx. A prebuild PDF can be found in `docs/latex`.
To generate the documentation, use 
```bash
make html
```
in the `docs` directory for a `html` output or `make latexpdf` for a PDF. This requires an installation of LaTeX on the system.