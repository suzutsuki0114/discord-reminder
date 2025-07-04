import os
from os.path import join, dirname
from dotenv import load_dotenv

# load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")
CHANNEL = os.environ.get("CHANNEL")
MESSAGE = os.environ.get("MESSAGE")

