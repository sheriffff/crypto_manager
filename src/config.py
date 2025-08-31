WHITELISTED_ASSETS = ["XXBT", "XETH", "ZUSD"]

asset_to_step = {
    "XXBT": 0.001,
    "XETH": 0.01,
    "ZUSD": 10,
}

pair_2_assets = {
    'XXBTZUSD': ('XXBT', 'ZUSD'),
    'XETHZUSD': ('XETH', 'ZUSD'),
    'XETHXXBT': ('XETH', 'XXBT'),
}

assets_2_pair = {v: k for k, v in pair_2_assets.items()}
