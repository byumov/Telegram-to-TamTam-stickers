import json
import logging
import random
import zipfile
from dataclasses import dataclass
from multiprocessing.dummy import Pool
from string import ascii_letters
from tempfile import TemporaryDirectory
from typing import List

import requests

from ImageConverter import ImageConverter

TELEGRAM_API_BASE_URL = "https://api.telegram.org"


class TGStickerDownloaderException(Exception):
    pass

class StickersSetNotFoundException(TGStickerDownloaderException):
    pass


@dataclass
class Sticker:
    file_id: str
    file_bytes: bytes
    emoji: str

@dataclass
class StickersSet:
    name: str
    title: str
    stickers: List[Sticker]

@dataclass
class TGFile:
    file_id: str
    file_unique_id: str 
    file_size: int
    file_path: str



class TGStickerDownloader:

    def __init__(self, tg_bot_token):
        self.base_api_url = f"{TELEGRAM_API_BASE_URL}/bot{tg_bot_token}"
        self.base_file_url = f"{TELEGRAM_API_BASE_URL}/file/bot{tg_bot_token}"
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

    def get_sticker_pack_by_name(self, name) -> StickersSet:
        method = "getStickerSet"
        try:
            res = self.api_request(method, params={"name": name})
        #  TODO: better exceptions and error messages
        except Exception:
            raise StickersSetNotFoundException("can't get pack from telegram")
        self.log.debug("resp: %s", json.dumps(res))
        stickers = []
        for s in res['result']['stickers']:
            stickers.append(Sticker(
                file_id=s['file_id'],
                emoji=s['emoji'],
                file_bytes=b""
            ))
        return StickersSet(res['result']['name'], res['result']['title'], stickers)

    def get_file(self, file_id) -> TGFile:
        method = "getFile"
        res = self.api_request(method, {"file_id": file_id})['result']
        return TGFile(res['file_id'], res['file_unique_id'], res['file_size'], res['file_path'])

    def download_file(self, file_path) -> bytes:
        res = requests.get(f"{self.base_file_url}/{file_path}")
        return res.content

    def api_request(self, method : str, params : dict=None) -> dict:
        url = f"{self.base_api_url}/{method}"
        self.log.debug("url: %s, params: %s", url, params)
        resp = requests.Response()  # type: requests.Response
        try:
            resp = requests.get(url, params=params)
        except requests.RequestException as e:
            self.log.error("can't send http request to telegram api: %s", e)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise TGStickerDownloaderException(f"telegram API error, status code: {resp.status_code}, text: {resp.text}")


    def create_tamtam_zip(self, tg_set_name: str) -> str:
        """return path to zip archive with stickers in TamTam format"""
        s_set = self.get_sticker_pack_by_name(tg_set_name)
        p = Pool(10)
        result_files = []  # type: List[str]
        with TemporaryDirectory(suffix=s_set.name) as tmpdir:
            p.starmap(self.proceed_sticker,  [(x, tmpdir, s_set.name, result_files) for x in s_set.stickers])
            zip_name = f"{s_set.name}.zip"
            with zipfile.ZipFile(zip_name, "w") as zf:
                for sticker_file in result_files:
                    self.log.debug("add to archive: %s", sticker_file)
                    zf.write(sticker_file, arcname=sticker_file.split("/")[-1])
        return zip_name


    def proceed_sticker(self, sticker: Sticker, tmp_dir : str, pack_name : str, result: list):
        c = ImageConverter()
        self.log.info("proceed %s", sticker.file_id)
        st_file = self.get_file(sticker.file_id)
        sticker.file_bytes = self.download_file(st_file.file_path)
        sticker.file_bytes = c.convert_to_tt_format(sticker.file_bytes)
        rnd_postfix = ''.join(random.choice(ascii_letters) for _ in range(5))
        file_path = f"{tmp_dir}/{pack_name}_{rnd_postfix}.png"
        result.append(file_path)
        with open(file_path, "wb") as fb:
            fb.write(sticker.file_bytes)
