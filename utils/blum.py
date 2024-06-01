import random
from utils.core import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestWebView
import asyncio
from urllib.parse import unquote
from data import config
import aiohttp
from fake_useragent import UserAgent
from utils.core.register import lang_code_by_phone


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
        self.proxy = f"http://{proxy}" if proxy is not None else None

        if proxy:
            proxy = {
                "scheme": config.PROXY_TYPE,
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
            lang_code=lang_code_by_phone(phone_number)
        )

        headers = {'User-Agent': UserAgent(os='android').random}
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=aiohttp.TCPConnector(verify_ssl=False))

    async def need_new_login(self):
        if (await self.session.get("https://gateway.blum.codes/v1/user/me", proxy=self.proxy)).status == 200:
            return False
        else:
            return True

    @retry_async()
    async def friend_claim(self):
        r = await (await self.session.get('https://gateway.blum.codes/v1/friends/balance', proxy=self.proxy)).json()
        if r.get('amountForClaim') is not None and float(r.get('amountForClaim')) and r.get('canClaim'):
            resp = await self.session.post("https://gateway.blum.codes/v1/friends/claim", proxy=self.proxy)
            claim_balance = (await resp.json()).get("claimBalance")
            logger.success(f"Thread {self.thread} | {self.account} | Claim friends reward: {claim_balance}")

    async def logout(self):
        await self.session.close()

    async def stats(self):
        await asyncio.sleep(random.uniform(*config.DELAYS['ACCOUNT']))
        await self.login()

        r = await (await self.session.get("https://game-domain.blum.codes/api/v1/user/balance", proxy=self.proxy)).json()
        points = r.get('availableBalance')
        plat_passes = r.get('playPasses')

        await asyncio.sleep(random.uniform(5, 7))

        r = await (await self.session.get("https://gateway.blum.codes/v1/friends/balance", proxy=self.proxy)).json()
        limit_invites = r.get('limitInvitation')
        referral_token = r.get('referralToken')
        if referral_token is not None:
            referral_link = 't.me/BlumCryptoBot/app?startapp=ref_' + referral_token
        else:
            logger.error(f"Thread {self.thread} |  {self.account} |Referral token is None")
            referral_link = None

        await asyncio.sleep(random.uniform(5, 7))

        r = await (await self.session.get("https://gateway.blum.codes/v1/friends", proxy=self.proxy)).json()
        referrals = len(r.get('friends'))

        await self.logout()

        await self.client.connect()
        me = await self.client.get_me()
        phone_number, name = "'" + me.phone_number, f"{me.first_name} {me.last_name if me.last_name is not None else ''}"
        await self.client.disconnect()

        proxy = self.proxy.replace('http://', "") if self.proxy is not None else '-'

        return [phone_number, name, points, str(plat_passes), str(referrals), limit_invites, referral_link, proxy]

    @retry_async()
    async def tasks(self):
        for task in await self.get_tasks():
            if task['status'] == 'CLAIMED' or task['title'] in config.BLACKLIST_TASKS: continue

            if task['status'] == "NOT_STARTED":
                await self.start_complete_task(task)
                await asyncio.sleep(random.uniform(15, 20))
            elif task['status'] == 'STARTED':
                await asyncio.sleep(random.uniform(15, 20))

            if await self.claim_task(task):
                logger.success(f"Thread {self.thread} | {self.account} | Completed task «{task['title']}»")
            else:
                logger.error(f"Thread {self.thread} | {self.account} | Failed complete task «{task['title']}»")

    async def claim_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/claim', proxy=self.proxy)
        return (await resp.json()).get('status') == "CLAIMED"

    async def start_complete_task(self, task: dict):
        resp = await self.session.post(f'https://game-domain.blum.codes/api/v1/tasks/{task["id"]}/start', proxy=self.proxy)

    async def get_tasks(self):
        resp = await self.session.get('https://game-domain.blum.codes/api/v1/tasks', proxy=self.proxy)
        return await resp.json()

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
            await asyncio.sleep(37)

            msg, points = await self.claim_game(game_id)
            if isinstance(msg, bool) and msg:
                logger.success(f"Thread {self.thread} | {self.account} | Finish play in game!; reward: {points}")
            else:
                logger.error(f"Thread {self.thread} | {self.account} | Couldn't play game; msg: {msg}")
                await asyncio.sleep(random.uniform(*config.DELAYS['ERROR_PLAY']))

            play_passes -= 1

    @retry_async()
    async def claim_daily_reward(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/daily-reward?offset=-180", proxy=self.proxy)
        if await resp.text() == 'OK':
            logger.success(f"Thread {self.thread} | {self.account} | Claimed daily reward!")

    async def start_game(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/game/play", proxy=self.proxy)
        return (await resp.json()).get("gameId")

    async def claim_game(self, game_id: str):
        points = random.randint(*config.POINTS)
        json_data = {"gameId": game_id, "points": points}

        resp = await self.session.post("https://game-domain.blum.codes/api/v1/game/claim", json=json_data, proxy=self.proxy)
        txt = await resp.text()

        return True if txt == 'OK' else txt, points

    async def claim(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/claim", proxy=self.proxy)
        resp_json = await resp.json()

        return int(resp_json.get("timestamp")/1000), resp_json.get("availableBalance")

    async def start(self):
        resp = await self.session.post("https://game-domain.blum.codes/api/v1/farming/start", proxy=self.proxy)

    async def balance(self):
        resp = await self.session.get("https://game-domain.blum.codes/api/v1/user/balance", proxy=self.proxy)
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

        json_data = {"query": query}

        resp = await self.session.post("https://gateway.blum.codes/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP", json=json_data, proxy=self.proxy)
        resp_json = await resp.json()

        self.session.headers['Authorization'] = "Bearer " + resp_json.get("token").get("access")
        return True

    async def get_tg_web_data(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestWebView(
                peer=await self.client.resolve_peer('BlumCryptoBot'),
                bot=await self.client.resolve_peer('BlumCryptoBot'),
                platform='android',
                from_bot_menu=False,
                url='https://telegram.blum.codes/'
            ))

            auth_url = web_view.url
            await self.client.disconnect()
        except:
            return None
        return unquote(string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))
