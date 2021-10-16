
import logging
from dataclasses import dataclass
from time import sleep
import os

import requests
from aiohttp import web

from .TelegramStickerDownloader import (StickersSetNotFoundException, TGStickerDownloader)


@dataclass
class UploadResult:
    file_id: int
    token: str

@dataclass
class update:
    sender_id: int
    sender_name: str
    sender_username: str
    message_text: str
    update_type: str

class TamTamBot():

    routes = web.RouteTableDef()

    def __init__(self, tt_bot_token: str, telegram_bot_token: str):
        self.base_url = "https://botapi.tamtam.chat"
        self.token = tt_bot_token
        self.tg_client = TGStickerDownloader(telegram_bot_token)
        self.log = logging.getLogger()


    def api_request(self, method: str, params: dict=None):
        if params is None:
            params = {}
        params['access_token'] = self.token
        res = requests.get(f"{self.base_url}/{method}", params=params)  # type: requests.Response
        if res.status_code == 200:
            return res.text
        else:
            raise Exception(f"TT API err: {res.status_code}")

    def get_updates(self):
        return self.api_request("updates")

    async def proceed(self, request):
        print("values:", request.values)
        print("query_string:", request.query_string)
        print("json:", request.json)
        data = await request.json()
        u = update(
            data['message']['sender']['user_id'],
            data['message']['sender']['name'],
            data['message']['sender']['username'],
            data['message']['body']['text'],
            data['update_type']
        )

        tg_set_name = u.message_text

        self.send_message(u.sender_id, f"Один момент, я уже готовлю архив со стикерами из пака:\n{tg_set_name}: https://t.me/addstickers/{tg_set_name}")
        try:
            self.tg_client.get_sticker_pack_by_name(tg_set_name)
        except StickersSetNotFoundException:
            text = "Привет! Я могу скачать твой любимый набор стикеров с Telegram и помогу загрузить их в TamTam\n" \
                    "Просто пришли мне имя пака.\n" \
                    f"Я не нашел в Telegram пак с именем '{tg_set_name}' 😢\n" \
                    "Пришли мне другое имя и попробуем еще разок!\n" \
                    "Узнать имя любимого пака можно в клиенте Telergam, или поискать здесь: https://tlgrm.ru/stickers"
            self.send_message(u.sender_id, text)
            return web.Response()

        zip_name = self.tg_client.create_tamtam_zip(u.message_text)

        #  send zip to user
        zip_file = self.upload_file(zip_name)
        attach = {
            "type": "file",
            "payload": {
                "token": zip_file.token
            }
        }
        text = "Готово 🥳\nЧтобы создать пак в ТамТам надо еще немного покликать:\n" \
                "Пишем боту в одноклассниках(ссылки в ТТ на него нет 🤷‍♂️): https://ok.ru/okstickers\n" \
                "Делаем все по онструкции от бота okstickers. Примерно так:\n" \
                "- жмем \"Создать новый набор стикеров\"\n" \
                "- отправляем полученный тут zip со стикерами\n" \
                "- жмем \"Закончить добавление\"\n" \
                "- пишем имя, как пак будет называться в ТТ и ОК(удобно называть так же, как оригинал в Telegram)" \
                "- жмем \"Опубликовать\"\n" \
                "- ...\n" \
                "Думаешь, это все? А вот и нет. Чтобы найти свои стикеры надо открыть Одноклассники и открыть любую периписку. Именно там, в Одноклассниках, будет видно новый пак. Скорее же отправьте стикер в любой чат! После этого, можно открыть эту периписку в ТТ и оттуда добавить пак в ТТ. Такие дела. Вот теперь все, можно загружать следующий 🙂"

        self.send_message(u.sender_id, text, attach=attach)

        return web.Response()


    def get_upload_url(self, file_type="file"):
        params = {
            "access_token": self.token,
            "type": file_type
        }
        # TODO exceptions
        res = requests.post(f"{self.base_url}/uploads", params=params).json()
        self.log.debug("upload url: %s", res)
        return res['url']

    def upload_file(self, file_path: str) -> UploadResult:
        upload_url = self.get_upload_url()
        with open(file_path,'rb') as fb:
            file_to_upload = {'file': (f'{file_path.split("/")[-1]}', fb, 'multipart/form-data')}
            res = requests.post(upload_url, files=file_to_upload).json()
            os.remove(file_path)
        return UploadResult(res['fileId'], res['token'])


    def send_message(self, user_id: int, text: str, attach: dict=None):
        param = {
            "access_token": self.token,
            "user_id": user_id
        }
        data = {
            "text": text
        }
        if attach is not None:
            data['attachments'] = []
            data['attachments'].append(attach)

        not_ok = True
        max_tries = 5
        sleep_time = 1
        while not_ok:
            res = requests.post(f"{self.base_url}/messages", json=data, params=param)
            self.log.info("sending msg to user %s: %s", user_id, text)
            if res.status_code == 200:
                not_ok = False
            # https://dev.tamtam.chat/#operation/sendMessage
            # It may take time for the server to process your file (audio/video or any binary). 
            # While a file is not processed you can't attach it. It means the last step will fail with 400 error. 
            # Try to send a message again until you'll get a successful result.
            if res.status_code == 400 and "file.not.processed" in res.json()["message"]:
                self.log.debug("sleep and retry...")
                sleep(sleep_time)
                max_tries -= 1
                sleep_time += 1
                if max_tries == 0:
                    self.send_message(user_id, "Не получилось загрузить файл в ТамТам, попробуйте еще раз позже")
                    web.Response()
                continue

            if res.status_code != 200:
                self.log.error("can't send msg to user %s, statis: %s %s", user_id, res.status_code, res.text)

        self.log.debug("msg was sent")

    def run(self):
        app = web.Application()
        app.add_routes([web.post('/', self.proceed)])
        web.run_app(app, port="19999")
