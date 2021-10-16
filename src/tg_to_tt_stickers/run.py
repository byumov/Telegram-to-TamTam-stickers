import logging
import os
import sys

from .TamTamBot import TamTamBot

logging.basicConfig()
log = logging.getLogger()
logging.getLogger('PIL').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
log.setLevel(logging.DEBUG)


def run():
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if tg_token is None:
        print("env var TELEGRAM_BOT_TOKEN must be set")
        sys.exit(1)

    tt_token = os.getenv("TAMTAM_BOT_TOKEN")
    if tt_token is None:
        print("env var TAMTAM_BOT_TOKEN must be set")
        sys.exit(1)

    b = TamTamBot(tt_token, tg_token)
    b.run()
