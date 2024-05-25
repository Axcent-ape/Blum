from utils.blum import BlumBot
from asyncio import sleep
from random import randint, uniform
from data import config
from utils.core import logger
import datetime
import pandas as pd
from utils.telegram import Accounts
import asyncio
from itertools import zip_longest
from utils.core import get_all_lines


async def start(thread: int, account: str, proxy: [str, None]):
    blum = BlumBot(account=account, thread=thread, proxy=proxy)

    await sleep(uniform(*config.DELAYS['ACCOUNT']))
    await blum.login()

    while True:
        try:
            msg = await blum.claim_daily_reward()
            if isinstance(msg, bool) and msg:
                logger.success(f"Thread {thread} | Claimed daily reward!")

            timestamp, start_time, end_time, play_passes = await blum.balance()

            await blum.play_game(play_passes)
            await sleep(uniform(5, 10))

            for task in await blum.get_tasks():
                if task['status'] == 'CLAIMED' or task['title'] in config.BLACKLIST_TASKS: continue

                if task['status'] == "NOT_STARTED":
                    await blum.start_complete_task(task)
                    await sleep(uniform(10, 15))
                elif task['status'] == 'STARTED':
                    await sleep(uniform(10, 15))

                if await blum.claim_task(task):
                    logger.success(f"Thread {thread} | Completed task «{task['title']}»")
                else:
                    logger.error(f"Thread {thread} | Failed complete task «{task['title']}»")

            timestamp, start_time, end_time, play_passes = await blum.balance()

            if start_time is None and end_time is None:
                await blum.start()
                logger.info(f"Thread {thread} | Start farming!")

            elif start_time is not None and end_time is not None and timestamp >= end_time:
                await blum.refresh()
                timestamp, balance = await blum.claim()
                logger.success(f"Thread {thread} | Claimed reward! Balance: {balance}")

            else:
                logger.info(f"Thread {thread} | Sleep {end_time - timestamp} seconds!")
                await sleep(end_time - timestamp)

            await sleep(10)
        except Exception as e:
            logger.error(f"Thread {thread} | Error: {e}")


async def stats():
    accounts = await Accounts().get_accounts()
    proxys = get_all_lines("data/proxy.txt")

    tasks = []
    for thread, (account, proxy) in enumerate(zip_longest(accounts, proxys)):
        if not account: break
        tasks.append(asyncio.create_task(BlumBot(account=account, thread=thread, proxy=proxy).stats()))

    data = await asyncio.gather(*tasks)

    path = f"statistics/statistics_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
    columns = ['Phone number', 'Name', 'Points', 'Play passes', 'Referrals', 'Limit invites', 'Referral link']

    df = pd.DataFrame(data, columns=columns)
    df['Name'] = df['Name'].astype(str)
    df.to_csv(path, index=False, encoding='utf-8-sig')

    logger.success(f"Saved statistics to {path}")
