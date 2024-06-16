import pyrogram
from loguru import logger
from data import config
from utils.core.file_manager import save_to_json


async def create_sessions():
    while True:
        session_name = input('\nInput the name of the session (press Enter to exit): ')
        if not session_name: return

        proxy = input("Input the proxy in the format login:password@ip:port (press Enter to use without proxy): ")
        if proxy:
            client_proxy = {
                "scheme": config.PROXY_TYPES['TG'],
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }
        else:
            client_proxy, proxy = None, None

        phone_number = (input("Input the phone number of the account: ")).replace(' ', '')
        phone_number = '+' + phone_number if not phone_number.startswith('+') else phone_number

        client = pyrogram.Client(
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            name=session_name,
            workdir=config.WORKDIR,
            phone_number=phone_number,
            proxy=client_proxy,
            lang_code='ru'
        )

        async with client:
            me = await client.get_me()

        save_to_json(f'{config.WORKDIR}accounts.json', dict_={
            "session_name": session_name,
            "phone_number": phone_number,
            "proxy": proxy
        })
        logger.success(f'Added a account {me.username} ({me.first_name}) | {me.phone_number}')