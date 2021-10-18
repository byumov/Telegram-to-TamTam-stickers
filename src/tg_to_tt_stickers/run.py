import logging
import os
import sys

from .TamTamBot import TamTamBot

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
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
    log.info("starting bot...")
    tt_bot = TamTamBot(tt_token, tg_token)
    tt_bot.run()
