import logging
from dataclasses import dataclass
from time import sleep
import os
from typing import List

import requests
from aiohttp import web

from .TelegramStickerDownloader import TGStickerDownloader


@dataclass
class UploadResult:
    file_id: int
    token: str

@dataclass
class User:
    user_id: int
    name: str
    username: str

@dataclass
class MessageBody:
    text: str

@dataclass
class Message:
    sender: User
    body: MessageBody
# user add the bot first time
@dataclass
class UpdateBotStarted:
    chat_id: int
    user: User


# user send a message to bot
@dataclass
class UpdateMessageCreated:
    message: Message

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

    def proceed_bot_started(self, data):
        update = UpdateBotStarted(
            data['chat_id'],
            User(
                data['user']['user_id'],
                data['user'].get('name', ""),
                data['user'].get('username', ""),
            )
        )
        self.send_message(update.user.user_id, 
                            "Привет 👋\nЯ помогу скачать твой любимый набор стикеров "
                            "из Telegram и расскажу, как загрузить его в TamTam\n" \
                            "Просто пришли мне имя стикер-пака\n")
        return web.Response()

    def proceed_message_created(self, data):
        if 'sender' not in data['message']:
            self.log.error("got bad update: %s", data)
            return web.Response()
        update = UpdateMessageCreated(
            Message(
                User(
                    data['message']['sender']['user_id'],
                    data['message']['sender']['name'],
                    data['message']['sender'].get('username', "")
                ),
                MessageBody(data['message']['body'].get("text", ""))
            )
        )

        tg_set_name = update.message.body.text

        tg_set = self.tg_client.get_sticker_pack_by_name(tg_set_name)
        if tg_set is None:
            self.send_message(update.message.sender.user_id,
                                f"Я не нашел в Telegram пак с именем '{tg_set_name}' 😢\n" \
                                "Пришли мне другое имя и попробуем еще разок!\n" \
                                "Узнать имя любимого пака можно в клиенте Telergam, "
                                "или поискать здесь: https://tlgrm.ru/stickers\n" \
                                "")
            return web.Response()

        self.send_message(update.message.sender.user_id, 
                            f"Один момент, я уже готовлю архив со стикерами из пака:\n{tg_set_name}: "
                            f"https://t.me/addstickers/{tg_set_name}")
        try:
            zip_names = self.tg_client.create_tamtam_zip(tg_set)
        #  TODO: better except
        except Exception as err:
            self.log.error("error while proceed pack %s: %s",tg_set, err)
            self.send_message(update.message.sender.user_id, 
                            "Извини, что-то пошло не так 😢\nПопробуй другой пак.\n" \
                            "Замуть меня, если эти сообщения не перестают приходить. Я еще молод и скоро все будет лучше 😉")
            return web.Response()

        #  send zip to user
        zip_files = self.upload_files(zip_names)
        attachments = []
        for zip_file in zip_files:
            attachments.append({
                "type": "file",
                "payload": {
                    "token": zip_file.token
                }
            })

        text = "Готово 🥳\nЧтобы загрузить пак в ТамТам надо сделать еще пару кликов:\n" \
                "Пишем боту: https://tt.me/stickers\n" \
                "Делаем все по инструкции от бота. Примерно так:\n" \
                "- создать новый пак\n" \
                "- отправить полученный тут zip со стикерами, бот ответит, что все ок\n" \
                "- если архивов несколько - загрузить следующий\n" \
                "- ...\n" \
                "- PROFIT!\n"

        if len(attachments) == 1:
            self.send_message(update.message.sender.user_id, text, attachments=attachments)
        else:
            self.send_message(update.message.sender.user_id, text)
            self.send_message(update.message.sender.user_id, "Тебе немного не повезло, в исходном Telegram паке больше 50-ти стикеров.\n"\
                "ТамТам разрешает загрузить до 50 штук в одном архиве.\n"
                "Я пришлю несколько архивов, их нужно будет отправить боту (https://tt.me/stickers) по очереди, дожидаясь обработки предыдушего.")
            for attach in attachments:
                self.send_message(update.message.sender.user_id, "", attachments=[attach])

        return web.Response()

    async def proceed(self, request):
        data = await request.json()
        self.log.debug("got update from tamtam api: %s", data)

        if 'update_type' not in data:
            self.log.error("bad update without type: %s", data)
            return web.Response()

        if data['update_type'] == 'bot_started':
            self.proceed_bot_started(data)

        elif data['update_type'] == 'message_created':
            self.proceed_message_created(data)

        self.log.error("got unknown update type: %s", data)
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

    def upload_files(self, file_paths: List[str]) -> List[UploadResult]:
        upload_results = []
        for file_path in file_paths:
            upload_url = self.get_upload_url()
            with open(file_path,'rb') as fb:
                file_to_upload = {'file': (f'{file_path.split("/")[-1]}', fb, 'multipart/form-data')}
                res = requests.post(upload_url, files=file_to_upload).json()
                os.remove(file_path)
                upload_results.append(UploadResult(res['fileId'], res['token']))
        return upload_results


    def send_message(self, user_id: int, text: str, attachments: list=None, no_link_preview=True):
        param = {
            "access_token": self.token,
            "user_id": user_id,
            "disable_link_preview": no_link_preview
        }
        data = {
            "text": text
        }
        if attachments is not None:
            data['attachments'] = attachments

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
                    self.send_message(user_id, "Не получилось загрузить файл в ТамТам, попробуй еще раз позже")
                    return web.Response()
                continue

            if res.status_code != 200:
                self.log.error("can't send msg to user %s, statis: %s %s", user_id, res.status_code, res.text)
                return web.Response()

    def run(self):
        app = web.Application()
        app.add_routes([web.post('/', self.proceed)])
        web.run_app(app, port=19999)
