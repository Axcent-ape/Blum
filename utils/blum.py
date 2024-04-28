import random
from utils.core import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView, GetMessagesViews
import asyncio
from urllib.parse import unquote
from data import config
import aiohttp
from fake_useragent import UserAgent


class Start:
    def __init__(self, thread: int, account: str):
        self.thread = thread
        self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR)

        headers = {'User-Agent': UserAgent(os='android').random}
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True)

    async def main(self):
        await asyncio.sleep(random.uniform(config.ACC_DELAY[0], config.ACC_DELAY[1]))
        await self.login()

        while True:
            try:
                timestamp, start_time, end_time = await self.balance()

                if start_time is None and end_time is None:
                    await self.start()
                    logger.info(f"Thread {self.thread} | Start farming!")

                elif start_time is not None and end_time is not None and timestamp >= end_time:
                    timestamp, balance = await self.claim()
                    logger.success(f"Thread {self.thread} | Claimed reward! Balance: {balance}")

                else:
                    logger.info(f"Thread {self.thread} | Sleep {end_time-timestamp} seconds!")
                    await asyncio.sleep(end_time-timestamp)

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Thread {self.thread} | Error: {e}")

    async def claim(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/claim")
        resp_json = await resp.json()

        return int(resp_json.get("timestamp")/1000), resp_json.get("availableBalance")

    async def start(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/start")

    async def balance(self):
        resp = await self.session.get("https://game-domain.blum.codes/api/v1/user/balance")
        resp_json = await resp.json()

        timestamp = resp_json.get("timestamp")
        if resp_json.get("timestamp"):
            start_time = resp_json.get("farming").get("startTime")
            end_time = resp_json.get("farming").get("endTime")

            return int(timestamp/1000), int(start_time/1000), int(end_time/1000)
        return int(timestamp/1000), None, None

    async def login(self):
        json_data = {"query": await self.get_tg_web_data()}

        resp = await self.session.post("https://gateway.blum.codes/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP", json=json_data)
        self.session.headers['Authorization'] = "Bearer " + (await resp.json()).get("token").get("access")

    async def get_tg_web_data(self):
        await self.client.connect()

        try:
            try:
                await self.client.join_chat("https://t.me/+3I58kRjC8uU4NTIy")
            except: pass

            async for msg in self.client.get_chat_history(-1002136959923, limit=1):
                msg_id = msg.id
            await self.client.invoke(GetMessagesViews(
                peer=await self.client.resolve_peer(-1002136959923),
                id=list(range(msg_id-random.randint(50, 100), msg_id + 1)),
                increment=True
            ))

        except: pass

        web_view = await self.client.invoke(RequestWebView(
            peer=await self.client.resolve_peer('BlumCryptoBot'),
            bot=await self.client.resolve_peer('BlumCryptoBot'),
            platform='android',
            from_bot_menu=False,
            url='https://telegram.blum.codes/'
        ))

        auth_url = web_view.url
        await self.client.disconnect()
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
