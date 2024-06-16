# api id, hash
API_ID = 1488
API_HASH = 'abcde1488'

DELAYS = {
    'ACCOUNT': [5, 15],  # delay between connections to accounts (the more accounts, the longer the delay)
    'PLAY': [5, 15],   # delay between play in seconds
    'ERROR_PLAY': [60, 180],    # delay between errors in the game in seconds
    'CLAIM': [600, 1800]   # delay in seconds before claim points every 8 hours
}
# points with each play game; max 280
POINTS = [240, 280]

PROXY_TYPES = {
    "TG": "socks5",  # proxy type for tg client. "socks4", "socks5" and "http" are supported
    "REQUESTS": "socks5"  # proxy type for requests. "http" for https and http proxys, "socks5" for socks5 proxy.
}

BLACKLIST_TASK = ["Launch Catizen's Kittyverse", 'Launch PixelTap']

# session folder (do not change)
WORKDIR = "sessions/"

# timeout in seconds for checking accounts on valid
TIMEOUT = 30
