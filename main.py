from utils.core import create_sessions
from utils.telegram import Accounts
from utils.blum import Start
import asyncio


async def main():
    print("Soft's author: https://t.me/ApeCryptor\n")
    action = int(input("Select action:\n1. Start claimer\n2. Create sessions\n\n> "))

    if action == 2:
        await create_sessions()

    if action == 1:
        accounts = await Accounts().get_accounts()

        tasks = []
        for thread, account in enumerate(accounts):
            tasks.append(asyncio.create_task(Start(account=account, thread=thread).main()))

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
