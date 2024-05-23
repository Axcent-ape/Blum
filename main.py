from utils.core import create_sessions
from utils.telegram import Accounts
from utils.blum import Start
import asyncio
from itertools import zip_longest
from utils.core import get_all_lines


async def main():
    print("Soft's author: https://t.me/ApeCryptor\n")
    action = int(input("Select action:\n1. Start claimer\n2. Create sessions\n\n> "))

    if action == 2:
        await create_sessions()

    if action == 1:
        accounts = await Accounts().get_accounts()
        proxys = get_all_lines("data/proxy.txt")

        tasks = []
        for thread, (account, proxy) in enumerate(zip_longest(accounts, proxys)):
            if not account: break
            tasks.append(asyncio.create_task(Start(account=account, thread=thread, proxy=proxy).main()))

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
