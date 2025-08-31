import pandas as pd
import streamlit as st
import time

from config import WHITELISTED_ASSETS, asset_to_step
from kraken import KrakenAPI, Kraken
from utils import load_keys, round_sig_dict


key, secret = load_keys()
kraken_api_handler = KrakenAPI(key=key, secret=secret)
kraken = Kraken(kraken_api_handler)


def set_page_config():
    st.set_page_config(
        page_title="Cryptos Manager",
        page_icon="💰",
        layout="wide",  # Set layout to wide
    )

    st.title("Cryptos Manager (Kraken)")


def load_info():
    if not st.session_state.get("loaded"):
        update_info()
        st.session_state.loaded = True


def update_info():
    update_balances()
    update_prices()


def update_balances():
    balances = kraken.get_assets_balances()
    balances = round_sig_dict(balances, 3)

    balances_usd = {k: kraken.to_usd(k, v) for k, v in balances.items()}
    balances_usd = round_sig_dict(balances_usd, 3)

    st.session_state.balances = balances
    st.session_state.balances_usd = balances_usd


def update_prices():
    prices = kraken.get_current_prices()
    prices = {k: round(v) for k, v in prices.items()}
    st.session_state.prices = prices


def reset_trading_volumes():
    st.session_state.asset_volume = 0
    st.session_state.usd_volume = 0


def update_asset_volume(asset_price):
    print("a")
    st.session_state.asset_volume = st.session_state.usd_volume / asset_price


def update_usd_volume(asset_price):
    print("u")
    st.session_state.usd_volume = st.session_state.asset_volume * asset_price


def confirm_trade():
    st.success("Done!")

    progress_text = "Updating balances..."
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.02)
        my_bar.progress(percent_complete + 1, text=progress_text)

    update_info()
    st.rerun()


def get_last_trades(asset_filter=None):
    trades_data = kraken.get_trades_history()
    trades = trades_data.get('result', {}).get('trades', {})

    now = pd.Timestamp('now')
    cutoff = now - pd.DateOffset(months=24)

    sorted_trades = sorted(trades.values(), key=lambda x: x['time'], reverse=True)
    rows = []
    for trade in sorted_trades:
        trade_time = pd.to_datetime(trade['time'], unit='s')
        if trade_time < cutoff:
            continue
        pair = trade.get('pair', '')
        # Extract asset from pair (e.g., XBTUSD -> XBT)
        currency = pair.replace('USD', '').replace('Z', '').replace('X', '') if pair else ''
        # Filter by asset if needed
        if asset_filter:
            if asset_filter == 'BTC' and currency != 'BT':
                continue
            if asset_filter == 'ETH' and currency != 'ETH':
                continue
        # Format date as '25 Aug 2025'
        date = trade_time.strftime('%-d %b %Y')
        buy_sell = 'BUY' if trade['type'].lower() == 'buy' else 'SELL'
        # Amount in USD (cost), round to -1 decimals, with dollar sign
        try:
            amount_usd = f"${round(float(trade.get('cost', 0)), -1):,.0f}"
        except (ValueError, TypeError):
            amount_usd = "$0"
        # Price, round to -1 decimals
        try:
            price = round(float(trade.get('price', 0)), -1)
        except (ValueError, TypeError):
            price = 0
        rows.append({
            'Date': date,
            'Type': buy_sell,
            'Amount $': amount_usd,
            'Price': price
        })
    df = pd.DataFrame(rows)
    return df.head(10)


def main():
    set_page_config()
    load_info()

    st.button("UPDATE", on_click=update_info)

    col1, _, col2 = st.columns([2, 2, 1])

    with col1:
        balances_info = [{"asset": asset, "volume": volume, "volume_USD": st.session_state.balances_usd[asset]} for asset, volume in st.session_state.balances.items()]
        balances_df = pd.DataFrame(balances_info)

        balances_df.sort_values("volume_USD", ascending=False, inplace=True)
        balances_df.set_index("asset", inplace=True)

        balance_total = balances_df["volume_USD"].sum()

        st.header(f"My Balance: {round(balance_total)}$")
        st.dataframe(balances_df)

    with col2:
        st.header("Price Now")
        prices_df = pd.DataFrame(st.session_state.prices.items(), columns=["asset", "price_USD"])
        prices_df.sort_values("price_USD", ascending=False, inplace=True)
        prices_df.set_index("asset", inplace=True)
        st.dataframe(prices_df)

    trade_col, trades_btc, trades_eth = st.columns([1, 1, 1])
    with trade_col:
        st.header("Trade with USD")
        assets = [asset for asset in WHITELISTED_ASSETS if asset != "ZUSD"]
        asset = st.radio("Asset", assets, on_change=reset_trading_volumes)
        asset_price = st.session_state.prices.get(asset)

        col1, col2 = st.columns(2)
        volume_usd = col1.number_input("USD", step=asset_to_step["ZUSD"], key="usd_volume", on_change=update_asset_volume, kwargs={"asset_price": asset_price})
        volume_asset = col2.number_input(asset, step=asset_to_step[asset], key="asset_volume", on_change=update_usd_volume, kwargs={"asset_price": asset_price}, format="%.5f")

        st.text("")

        col1, col2, _ = st.columns(3)
        if col1.button(f"BUY {asset}"):
            if volume_usd > st.session_state.balances["ZUSD"]:
                st.error("Not enough USD funds")
            else:
                if kraken.buy_market(asset, volume_asset):
                    confirm_trade()
                else:
                    st.error("Something went wrong")

        if col2.button(f"SELL {asset}"):
            if volume_asset > st.session_state.balances[asset]:
                st.error(f"Not enough {asset} funds")
            else:
                if kraken.sell_market(asset, volume_asset):
                    confirm_trade()
                else:
                    st.error("Something went wrong")

    with trades_btc:
        st.header("Latest BTC Orders")
        last_btc_trades_df = get_last_trades(asset_filter="BTC")
        st.dataframe(last_btc_trades_df, use_container_width=True, hide_index=True)

    with trades_eth:
        st.header("Latest ETH Orders")
        last_eth_trades_df = get_last_trades(asset_filter="ETH")
        st.dataframe(last_eth_trades_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
