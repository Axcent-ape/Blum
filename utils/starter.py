from utils.blum import BlumBot
from asyncio import sleep
from random import uniform
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
    if await blum.login() is None:
        return

    while True:
        try:
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
                logger.info(f"Thread {thread} | Start farming!")

            elif start_time is not None and end_time is not None and timestamp >= end_time:
                timestamp, balance = await blum.claim()
                logger.success(f"Thread {thread} | Claimed reward! Balance: {balance}")

            else:
                logger.info(f"Thread {thread} | Sleep {end_time - timestamp} seconds!")
                await sleep(end_time - timestamp)

                if await blum.login() is None:
                    return

            await sleep(30)
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
