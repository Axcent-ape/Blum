from utils.blum import BlumBot
from asyncio import sleep
from random import uniform
from data import config
from utils.core import logger
import datetime
import pandas as pd
from utils.telegram import Accounts
import asyncio
from aiohttp.client_exceptions import ContentTypeError


async def start(thread: int, session_name: str, phone_number: str, proxy: [str, None]):
    blum = BlumBot(session_name=session_name, phone_number=phone_number, thread=thread, proxy=proxy)
    account = session_name + '.session'

    await sleep(uniform(*config.DELAYS['ACCOUNT']))
    if await blum.login() is None:
        return

    while True:
        try:
            await asyncio.sleep(5)
            if await blum.need_new_login():
                if await blum.login() is None:
                    return

            await blum.claim_daily_reward()
            await sleep(uniform(2, 8))

            await blum.friend_claim()
            await sleep(uniform(2, 8))

            await blum.play_game()
            await sleep(uniform(5, 8))

            await blum.tasks()
            await sleep(uniform(5, 8))

            timestamp, start_time, end_time, play_passes = await blum.balance()

            if start_time is None and end_time is None:
                await blum.start()
                logger.info(f"Thread {thread} | {account} | Start farming!")

            elif start_time is not None and end_time is not None and timestamp >= end_time:
                timestamp, balance = await blum.claim()
                logger.success(f"Thread {thread} | {account} | Claimed reward! Balance: {balance}")

            else:
                logger.info(f"Thread {thread} | {account} | Sleep {end_time - timestamp} seconds!")
                await sleep(end_time - timestamp)

            await sleep(30)
        except ContentTypeError as e:
            logger.error(f"Thread {thread} | {account} | Error: {e}")
            await asyncio.sleep(120)

        except Exception as e:
            logger.error(f"Thread {thread} | {account} | Error: {e}")


async def stats():
    accounts = await Accounts().get_accounts()

    tasks = []
    for thread, account in enumerate(accounts):
        session_name, phone_number, proxy = account.values()
        tasks.append(asyncio.create_task(BlumBot(session_name=session_name, phone_number=phone_number, thread=thread, proxy=proxy).stats()))

    data = await asyncio.gather(*tasks)

    path = f"statistics/statistics_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
    columns = ['Phone number', 'Name', 'Points', 'Play passes', 'Referrals', 'Limit invites', 'Referral link', 'Proxy (login:password@ip:port)']

    df = pd.DataFrame(data, columns=columns)
    df['Name'] = df['Name'].astype(str)
    df.to_csv(path, index=False, encoding='utf-8-sig')

    logger.success(f"Saved statistics to {path}")
