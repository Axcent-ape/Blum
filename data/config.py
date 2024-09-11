# api id, hash
API_ID = 1488
API_HASH = 'abcde1488'

REF_LINK = 'https://t.me/BlumCryptoBot/app?startapp=ref_GY2Vsk7swg'

DELAYS = {
    "RELOGIN": [5, 7],  # delay after a login attempt
    'ACCOUNT': [5, 15],  # delay between connections to accounts (the more accounts, the longer the delay)
    'PLAY': [5, 15],   # delay between play in seconds
    'ERROR_PLAY': [5, 8],    # delay between errors in the game in seconds
    'CLAIM': [600, 1800],   # delay in seconds before claim points every 8 hours
    'GAME': [35, 37],  # delay after the start of the game
    'TASK_COMPLETE': [2, 3],  # delay after completed the task
    'TASK_ACTION': [5, 10]  # delay after start task
}

# if you need play in the game
PLAY_GAME = True

# points with each play game; max 280
POINTS = [240, 280]

BLACKLIST_TASK = ['Join or create tribe']

PROXY = {
    "USE_PROXY_FROM_FILE": False,  # True - if use proxy from file, False - if use proxy from accounts.json
    "PROXY_PATH": "data/proxy.txt",  # path to file proxy
    "TYPE": {
        "TG": "http",  # proxy type for tg client. "socks4", "socks5" and "http" are supported
        "REQUESTS": "http"  # proxy type for requests. "http" for https and http proxys, "socks5" for socks5 proxy.
        }
}

# session folder (do not change)
WORKDIR = "sessions/"

# timeout in seconds for checking accounts on valid
TIMEOUT = 30
