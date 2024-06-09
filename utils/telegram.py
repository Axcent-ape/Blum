import asyncio
import os
from data import config
from pyrogram import Client
from utils.core import logger, load_from_json


class Accounts:
    def __init__(self):
        self.workdir = config.WORKDIR
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH

    @staticmethod
    def get_available_accounts(sessions: list):
        accounts_from_json = load_from_json('sessions/accounts.json')

        if not accounts_from_json:
            raise ValueError("Have not account's in sessions/accounts.json")

        available_accounts = []
        for session in sessions:
            for saved_account in accounts_from_json:
                if saved_account['session_name'] == session:
                    available_accounts.append(saved_account)
                    break

        return available_accounts

    def pars_sessions(self):
        sessions = []
        for file in os.listdir(self.workdir):
            if file.endswith(".session"):
                sessions.append(file.replace(".session", ""))

        logger.info(f"Searched sessions: {len(sessions)}.")
        return sessions

    async def check_valid_account(self, account: dict):
        session_name, phone_number, proxy = account.values()

        try:
            proxy_dict = {
                "scheme": config.PROXY_TYPE,
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            } if proxy else None

            client = Client(name=session_name, api_id=self.api_id, api_hash=self.api_hash, workdir=self.workdir,
                            proxy=proxy_dict)

            connect = await asyncio.wait_for(client.connect(), timeout=config.TIMEOUT)
            if connect:
                await client.get_me()
                await client.disconnect()
                return account
            else:
                await client.disconnect()
        except:
            pass

    async def check_valid_accounts(self, accounts: list):
        logger.info(f"Checking accounts for valid...")

        tasks = []
        for account in accounts:
            tasks.append(asyncio.create_task(self.check_valid_account(account)))

        v_accounts = await asyncio.gather(*tasks)
        valid_accounts = [valid_accounts for valid_accounts in v_accounts if valid_accounts is not None]

        logger.success(f"Valid accounts: {len(valid_accounts)}; Invalid: {len(accounts)-len(valid_accounts)}")
        return valid_accounts

    async def get_accounts(self):
        sessions = self.pars_sessions()
        available_accounts = self.get_available_accounts(sessions)

        if not available_accounts:
            raise ValueError("Have not available accounts!")
        else:
            logger.success(f"Search available accounts: {len(available_accounts)}.")

        valid_accounts = await self.check_valid_accounts(available_accounts)

        if not valid_accounts:
            raise ValueError("Have not valid sessions")
        else:
            return valid_accounts
