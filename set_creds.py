"""Set Creds.

Leverages Keyring to add your credentials for each portal and then retrieves them in code.
author: ehgp
"""
from getpass import getpass
from getpass import getuser
import keyring
from pathlib import Path
import os
import yaml
import logging
import logging.config
import datetime as dt

# Paths
path = Path(os.getcwd())

# Logging
log_config = Path(path, "log_config.yaml")
timestamp = "{:%Y_%m_%d_%H_%M_%S}".format(dt.datetime.now())
with open(log_config, "r") as log_file:
    config_dict = yaml.safe_load(log_file.read())
    # Append date stamp to the file name
    log_filename = config_dict["handlers"]["file"]["filename"]
    base, extension = os.path.splitext(log_filename)
    base2 = "set_creds"
    log_filename = "{}{}{}{}".format(base, base2, timestamp, extension)
    config_dict["handlers"]["file"]["filename"] = log_filename
    logging.config.dictConfig(config_dict)
logger = logging.getLogger(__name__)

# Leverages Windows Credential Manager and Mac Keychain to store credentials
# and also makes environment variables that store your credentials in your computer
users = [
    "YOUTUBE_EMAIL",
    "YOUTUBE_PASSWORD",
]
user = getuser()
for i in users:
    dsn = i
    prompt = input(f"Please input {dsn}: ")
    password = getpass(prompt=prompt, stream=None)
    keyring.set_password(dsn, user, password)
