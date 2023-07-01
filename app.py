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
    st.experimental_rerun()


def main():
    set_page_config()
    load_info()

    st.button("UPDATE", on_click=update_info)

    col1, col2 = st.columns([2, 1])

    with col1:
        balances_info = [{"asset": asset, "volume": volume, "volume_USD": st.session_state.balances_usd[asset]} for asset, volume in st.session_state.balances.items()]
        balances_df = pd.DataFrame(balances_info)

        balances_df.sort_values("volume_USD", ascending=False, inplace=True)
        balances_df.set_index("asset", inplace=True)

        balance_total = balances_df["volume_USD"].sum()

        st.header(f"My Balance: {round(balance_total)}$")
        st.dataframe(balances_df)

    with col2:
        st.header("Prices")
        prices_df = pd.DataFrame(st.session_state.prices.items(), columns=["asset", "price_USD"])
        prices_df.sort_values("price_USD", ascending=False, inplace=True)
        prices_df.set_index("asset", inplace=True)
        st.dataframe(prices_df)

    st.header("Trade with USD")
    assets = [asset for asset in WHITELISTED_ASSETS if asset != "ZUSD"]
    asset = st.columns(2)[0].selectbox("Asset", assets, on_change=reset_trading_volumes)
    asset_price = st.session_state.prices.get(asset)

    col1, col2, _, _ = st.columns(4)
    volume_asset = col1.number_input(asset, step=asset_to_step[asset], key="asset_volume", on_change=update_usd_volume, kwargs={"asset_price": asset_price}, format="%.5f")
    volume_usd = col2.number_input("USD", step=asset_to_step["ZUSD"], key="usd_volume", on_change=update_asset_volume, kwargs={"asset_price": asset_price})

    col1, col2, _, _ = st.columns(4)
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


if __name__ == "__main__":
    main()
