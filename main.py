from utils.core.telegram import Accounts
from utils.starter import start, stats
import asyncio
from data import config
from itertools import zip_longest
from utils.core import get_all_lines
import os


async def main():
    print("Soft's author: https://t.me/ApeCryptor\n")
    action = int(input("Select action:\n1. Start soft\n2. Get statistics\n3. Create sessions\n\n> "))

    if not os.path.exists('sessions'): os.mkdir('sessions')

    if config.PROXY['USE_PROXY_FROM_FILE']:
        if not os.path.exists(config.PROXY['PROXY_PATH']):
            with open(config.PROXY['PROXY_PATH'], 'w') as f:
                f.write("")
    else:
        if not os.path.exists('sessions/accounts.json'):
            with open("sessions/accounts.json", 'w') as f:
                f.write("[]")

    if action == 3:
        await Accounts().create_sessions()

    if action == 2:
        await stats()

    if action == 1:
        accounts = await Accounts().get_accounts()

        tasks = []

        for thread, account in enumerate(accounts):
            session_name, phone_number, proxy = account.values()
            tasks.append(asyncio.create_task(start(session_name=session_name, phone_number=phone_number, thread=thread, proxy=proxy)))

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
