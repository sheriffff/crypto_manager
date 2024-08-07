from datetime import datetime
import pandas as pd
import requests
import time

from config import WHITELISTED_ASSETS, assets_2_pair
from utils import get_kraken_signature, load_keys


class KrakenAPI:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.uri = 'https://api.kraken.com'
        self._headers = {
            'User-Agent': 'Kraken REST API',
            'API-Key': self.key,
        }

    def _query(self, urlpath, data=None):
        url = self.uri + urlpath

        if data is None:
            data = {}
        data['nonce'] = str(int(1000 * time.time()))

        headers = self._headers.copy()
        headers['API-Sign'] = get_kraken_signature(urlpath, data, self.secret)

        response = requests.post(url, data=data, headers=headers)
        return response.json()

    def get_assets_balances(self):
        return self._query('/0/private/Balance')

    def get_trades_history(self):
        return self._query('/0/private/TradesHistory')

    def get_ticker_info(self, pair):
        return self._query('/0/public/Ticker', data={'pair': pair})

    def get_order_book(self, pair):
        return self._query('/0/public/Depth', data={'pair': pair})

    def get_ohlc(self, pair, interval_mins):
        return self._query('/0/public/OHLC', data={'pair': pair, 'interval': interval_mins})

    def add_market_order(self, pair, buy_or_sell, volume):
        data = {
            'pair': pair,
            'type': buy_or_sell,
            'ordertype': "market",
            'volume': volume,
        }

        response = self._query('/0/private/AddOrder', data)
        return response


class Kraken:
    def __init__(self, kraken_api):
        self.api = kraken_api

    def get_assets_balances(self):
        assets_balances = self.api.get_assets_balances().get("result")
        assets_balances_relevant = {k: float(v) for k, v in assets_balances.items() if k in WHITELISTED_ASSETS}

        return assets_balances_relevant

    def get_current_prices(self):
        prices = {}
        for asset in WHITELISTED_ASSETS:
            if asset != "ZUSD":  # No need to get price for USD
                pair = assets_2_pair[(asset, "ZUSD")]
                ticker_info = self.api.get_ticker_info(pair).get("result")
                current_price = float(ticker_info.get(pair).get("c")[0])
                prices[asset] = current_price

        return prices

    def get_prices_history(self, pair, interval_mins=1):
        ohlc_history = self.api.get_ohlc(pair, interval_mins).get("result")
        ohlc_history = ohlc_history.get(pair)

        price_history = [{
            "time": datetime.fromtimestamp(ohlc_elem[0]),
            "price": float(ohlc_elem[4]),
            "open": float(ohlc_elem[1]),
            "high": float(ohlc_elem[2]),
            "low": float(ohlc_elem[3]),
            "close": float(ohlc_elem[4]),
        } for ohlc_elem in ohlc_history]
        price_history_df = pd.DataFrame(price_history)

        return price_history_df

    def to_usd(self, asset, asset_amount):
        if asset == "ZUSD":
            return asset_amount
        else:
            pair = assets_2_pair[(asset, "ZUSD")]
            ticker_info = self.api.get_ticker_info(pair).get("result")
            current_price = float(ticker_info.get(pair).get("c")[0])

            return asset_amount * current_price

    def from_usd(self, asset, usd_amount):
        return usd_amount / self.to_usd(asset, 1)

    def sell_market(self, asset, volume):
        """
        Sells asset to get USD
        """
        pair = assets_2_pair[(asset, "ZUSD")]
        response = self.api.add_market_order(pair, "sell", volume)

        if response["error"]:
            print(response["error"])
            return False
        else:
            return True

    def buy_market(self, asset, volume):
        """
        Buys asset with USD
        """
        pair = assets_2_pair[(asset, "ZUSD")]
        response = self.api.add_market_order(pair, "buy", volume)

        if response["error"]:
            print(response["error"])
            return False
        else:
            return True


def initialize_kraken_api():

    key, secret = load_keys()
    kraken_api = KrakenAPI(key=key, secret=secret)
    return Kraken(kraken_api)
