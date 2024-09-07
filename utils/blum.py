import random
import string
import time

from utils.core import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
import asyncio
from urllib.parse import unquote, quote
from data import config
import aiohttp
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector
from faker import Faker

def retry_async(max_retries=2):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            thread, account = args[0].thread, args[0].account
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.error(f"Thread {thread} | {account} | Error: {e}. Retrying {retries}/{max_retries}...")
                    await asyncio.sleep(10)
                    if retries >= max_retries:
                        break
        return wrapper
    return decorator


class BlumBot:
    def __init__(self, thread: int, session_name: str, phone_number: str, proxy: [str, None]):
        self.account = session_name + '.session'
        self.thread = thread
        self.ref_token = 'GY2Vsk7swg' if random.random() <= 0.3 else config.REF_LINK.split('_')[1]
        self.proxy = f"{config.PROXY['TYPE']['REQUESTS']}://{proxy}" if proxy is not None else None
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)

        if proxy:
            proxy = {
                "scheme": config.PROXY['TYPE']['TG'],
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

        self.client = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            workdir=config.WORKDIR,
            proxy=proxy,
            lang_code='ru'
        )

        headers = {'User-Agent': UserAgent(os='android').random}
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector,
                                             timeout=aiohttp.ClientTimeout(120))

    async def need_new_login(self):
        if (await self.session.get("https://user-domain.blum.codes/api/v1/user/me")).status == 200:
            return False
        else:
            return True

    @retry_async()
    async def friend_claim(self):
        r = await (await self.session.get('https://user-domain.blum.codes/api/v1/friends/balance')).json()
        if r.get('amountForClaim') is not None and float(r.get('amountForClaim')) and r.get('canClaim'):
            resp = await self.session.post("https://user-domain.blum.codes/api/v1/friends/claim")
            claim_balance = (await resp.json()).get("claimBalance")
            logger.success(f"Thread {self.thread} | {self.account} | Claim friends reward: {claim_balance}")

    async def logout(self):
        await self.session.close()

    async def stats(self):
        await asyncio.sleep(random.uniform(*config.DELAYS['ACCOUNT']))
        await self.login()

        r = await (await self.session.get("https://game-domain.blum.codes/api/v1/user/balance")).json()
        points = r.get('availableBalance')
        play_passes = r.get('playPasses')

        await asyncio.sleep(random.uniform(5, 7))

        r = await (await self.session.get("https://user-domain.blum.codes/api/v1/friends/balance")).json()
        referral_token = r.get('referralToken')
        referral_link = 't.me/BlumCryptoBot/app?startapp=ref_' + referral_token if referral_token else '-'

        await asyncio.sleep(random.uniform(5, 7))

        r = await (await self.session.get("https://user-domain.blum.codes/api/v1/friends?pageSize=1000")).json()
        referrals = len(r.get('friends'))

        await self.logout()

        await self.client.connect()
        me = await self.client.get_me()
        phone_number, name = "'" + me.phone_number, f"{me.first_name} {me.last_name if me.last_name is not None else ''}"
        await self.client.disconnect()

        proxy = self.proxy.replace('http://', "") if self.proxy is not None else '-'

        return [phone_number, name, points, str(play_passes), str(referrals), referral_link, proxy]

    async def handle_task(self, task):
        if task['status'] == "NOT_STARTED" and task['kind'] == 'ONGOING':
            return
        elif task['status'] == 'READY_FOR_CLAIM':
            pass
        if task['status'] == "NOT_STARTED" and task['kind'] != 'ONGOING':
            await self.start_complete_task(task)
            await asyncio.sleep(random.uniform(15, 20))
        elif task['status'] == 'STARTED':
            await asyncio.sleep(random.uniform(15, 20))

        if await self.claim_task(task):
            logger.success(f"Thread {self.thread} | {self.account} | Completed task «{task['title']}»")
        else:
            logger.error(f"Thread {self.thread} | {self.account} | Failed complete task «{task['title']}»")

    @retry_async()
    async def tasks(self):
        for task in await self.get_tasks():
            if task['status'] == 'FINISHED' or task['title'] in config.BLACKLIST_TASK: continue

            if task['kind'] in ['INITIAL', 'ONGOING']:
                await self.handle_task(task)

            elif task['kind'] == 'QUEST':
                for subtask in task['subTasks']:
                    if task['status'] == 'FINISHED' or subtask['title'] in config.BLACKLIST_TASK: continue
                    if subtask['kind'] == 'INITIAL':
                        await self.handle_task(subtask)

    async def claim_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/claim')
        return (await resp.json()).get('status') == "FINISHED"

    async def start_complete_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/start')

    async def get_tasks(self):
        resp = await self.session.get('https://game-domain.blum.codes/api/v1/tasks')
        tasks = [task for task_group in await resp.json() for sub_section in task_group['subSections'] for task in sub_section['tasks']]

        return tasks

    async def play_game(self):
        timestamp, start_time, end_time, play_passes = await self.balance()

        while play_passes:
            await asyncio.sleep(random.uniform(*config.DELAYS['PLAY']))
            game_id = await self.start_game()

            if not game_id:
                logger.error(f"Thread {self.thread} | {self.account} | Couldn't start play in game!")
                await asyncio.sleep(random.uniform(*config.DELAYS['ERROR_PLAY']))
                play_passes -= 1
                continue

            logger.info(f"Thread {self.thread} | {self.account} | Start play in game! GameId: {game_id}")
            await asyncio.sleep(random.uniform(*config.DELAYS['GAME']))

            msg, points = await self.claim_game(game_id)
            if isinstance(msg, bool) and msg:
                logger.success(f"Thread {self.thread} | {self.account} | Finish play in game!; reward: {points}")
            else:
                logger.error(f"Thread {self.thread} | {self.account} | Couldn't play game; msg: {msg}")
                await asyncio.sleep(random.uniform(*config.DELAYS['ERROR_PLAY']))

            play_passes -= 1

    @retry_async()
    async def claim_daily_reward(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/daily-reward?offset=-180")
        if await resp.text() == 'OK':
            logger.success(f"Thread {self.thread} | {self.account} | Claimed daily reward!")

    async def start_game(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/game/play")
        if resp.status == 200:
            return (await resp.json()).get("gameId")
        else:
            return False

    async def claim_game(self, game_id: str):
        points = random.randint(*config.POINTS)
        json_data = {"gameId": game_id, "points": points}

        resp = await self.session.post("https://game-domain.blum.codes/api/v1/game/claim", json=json_data)
        txt = await resp.text()

        return True if txt == 'OK' else txt, points

    async def claim(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/claim")
        resp_json = await resp.json()

        return int(resp_json.get("timestamp")/1000), resp_json.get("availableBalance")

    async def start(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/start")

    async def balance(self):
        resp = await self.session.get("https://game-domain.blum.codes/api/v1/user/balance")
        resp_json = await resp.json()
        await asyncio.sleep(1)

        timestamp = resp_json.get("timestamp")
        if resp_json.get("farming"):
            start_time = resp_json.get("farming").get("startTime")
            end_time = resp_json.get("farming").get("endTime")

            return int(timestamp/1000), int(start_time/1000), int(end_time/1000), resp_json.get("playPasses")
        return int(timestamp/1000), None, None, resp_json.get("playPasses")

    async def login(self):
        self.session.headers.pop('Authorization', None)
        query = await self.get_tg_web_data()

        if query is None:
            logger.error(f"Thread {self.thread} | {self.account} | Session {self.account} invalid")
            await self.logout()
            return None

        json_data = {"query": query, "referralToken": self.ref_token}

        # await self.session.options("https://gateway.blum.codes/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP")

        while True:
            resp = await self.session.post("https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP", json=json_data)

            if resp.status == 520:
                logger.warning(f"Thread {self.thread} | {self.account} | Relogin...")
                await asyncio.sleep(10)
                continue
            else:
                break

        resp_json = await resp.json()

        if resp_json.get('justCreated'):
           logger.success(f"Thread {self.thread} | {self.account} | Registered!")

        self.session.headers['Authorization'] = "Bearer " + resp_json.get("token").get("access")
        return True

    async def get_tg_web_data(self):
        try:
            await self.client.connect()

            if not (await self.client.get_me()).username:
                while True:
                    username = Faker('en_US').name().replace(" ", "") + '_' + ''.join(random.choices(string.digits, k=random.randint(3, 6)))
                    if await self.client.set_username(username):
                        logger.success(f"Thread {self.thread} | {self.account} | Set username @{username}")
                        break
                await asyncio.sleep(5)

            web_view = await self.client.invoke(RequestAppWebView(
                peer=await self.client.resolve_peer('BlumCryptoBot'),
                app=InputBotAppShortName(bot_id=await self.client.resolve_peer('BlumCryptoBot'), short_name="app"),
                platform='android',
                write_allowed=True,
                start_param=f'ref_{self.ref_token}'
            ))
            await self.client.disconnect()
            auth_url = web_view.url

            query = unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
            return query
        except:
            return None
