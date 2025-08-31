import pandas as pd
import streamlit as st
import time
import plotly.express as px
import matplotlib.pyplot as plt

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
            'Price': price,
            'Amount $': amount_usd,
        })
    df = pd.DataFrame(rows)
    return df.head(10)


def main():
    set_page_config()
    load_info()

    st.button("UPDATE", on_click=update_info)

    st.markdown("---")

    col_balances, _, col_prices, _, col_trade = st.columns([1.5, 0.5, 1, 0.5, 1.5])

    with col_balances:
        balances_info = [{"asset": asset, "volume": volume, "volume_USD": st.session_state.balances_usd[asset]} for asset, volume in st.session_state.balances.items()]
        balances_df = pd.DataFrame(balances_info)

        balances_df.sort_values("volume_USD", ascending=False, inplace=True)
        balances_df.set_index("asset", inplace=True)

        balance_total = balances_df["volume_USD"].sum()

        st.header(f"My Balance: {round(balance_total)}$")
        st.dataframe(balances_df)

    with col_prices:
        st.header("Price Now")
        prices_df = pd.DataFrame(st.session_state.prices.items(), columns=["asset", "price_USD"])
        prices_df["price_USD"] = prices_df["price_USD"].astype(float)
        prices_df.sort_values("price_USD", ascending=False, inplace=True)
        prices_df["price_USD"] = prices_df["price_USD"]
        prices_df.set_index("asset", inplace=True)
        st.dataframe(prices_df)

    with col_trade:
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

    st.markdown("---")

    trades_btc, _, trades_eth = st.columns([4, 1, 4])

    with trades_btc:
        st.header("Latest BTC Orders")
        last_btc_trades_df = get_last_trades(asset_filter="BTC")
        # Format Price column to one decimal
        last_btc_trades_df['Price'] = last_btc_trades_df['Price'].map(lambda x: f"{x:.1f}")
        def highlight_type(val):
            color = '#d4f8e8' if val == 'BUY' else '#ffd6d6'
            return f'background-color: {color}'
        def highlight_price(row):
            color = '#d4f8e8' if row['Type'] == 'BUY' else '#ffd6d6'
            return [f'background-color: {color}' if col == 'Price' else '' for col in row.index]
        styled_btc_df = last_btc_trades_df.style.applymap(highlight_type, subset=['Type']).apply(highlight_price, axis=1)
        st.dataframe(styled_btc_df, use_container_width=True, hide_index=True)
        # Matplotlib chart for BTC trades
        if not last_btc_trades_df.empty:
            chart_df = last_btc_trades_df.copy()
            chart_df['Timestamp'] = pd.to_datetime(chart_df['Date'], format='%d %b %Y')
            chart_df['AmountNum'] = chart_df['Amount $'].str.replace(r'[$,]', '', regex=True).astype(float)
            chart_df['Color'] = chart_df['Type'].map({'BUY': 'green', 'SELL': 'red'})
            def format_k(amount):
                if amount >= 1000:
                    return f"{amount/1000:.1f}k"
                else:
                    return f"{int(amount)}"
            fig, ax = plt.subplots()
            # Plot lines
            ax.plot(chart_df['Timestamp'], chart_df['Price'].astype(float), color='gray', linestyle='-', linewidth=1, zorder=1)
            # Plot dots and labels
            for idx, row in chart_df.iterrows():
                ax.scatter(row['Timestamp'], float(row['Price']), s=row['AmountNum']/chart_df['AmountNum'].max()*100+20, color=row['Color'], zorder=2)
                ax.text(row['Timestamp'], float(row['Price']), format_k(row['AmountNum']), fontsize=8, color=row['Color'], ha='left', va='bottom')
            ax.set_xlabel('Date')
            ax.set_ylabel('Price')
            ax.set_title('BTC Trades (Last 24 Months)')
            plt.xticks(rotation=45)
            st.pyplot(fig, use_container_width=True)

    with trades_eth:
        st.header("Latest ETH Orders")
        last_eth_trades_df = get_last_trades(asset_filter="ETH")
        # Format Price column to one decimal
        last_eth_trades_df['Price'] = last_eth_trades_df['Price'].map(lambda x: f"{x:.1f}")
        styled_eth_df = last_eth_trades_df.style.applymap(highlight_type, subset=['Type']).apply(highlight_price, axis=1)
        st.dataframe(styled_eth_df, use_container_width=True, hide_index=True)
        # Matplotlib chart for ETH trades
        if not last_eth_trades_df.empty:
            chart_df = last_eth_trades_df.copy()
            chart_df['Timestamp'] = pd.to_datetime(chart_df['Date'], format='%d %b %Y')
            chart_df['AmountNum'] = chart_df['Amount $'].str.replace(r'[$,]', '', regex=True).astype(float)
            chart_df['Color'] = chart_df['Type'].map({'BUY': 'green', 'SELL': 'red'})
            def format_k(amount):
                if amount >= 1000:
                    return f"{amount/1000:.1f}k"
                else:
                    return f"{int(amount)}"
            fig, ax = plt.subplots()
            ax.plot(chart_df['Timestamp'], chart_df['Price'].astype(float), color='gray', linestyle='-', linewidth=1, zorder=1)
            for idx, row in chart_df.iterrows():
                ax.scatter(row['Timestamp'], float(row['Price']), s=row['AmountNum']/chart_df['AmountNum'].max()*100+20, color=row['Color'], zorder=2)
                ax.text(row['Timestamp'], float(row['Price']), format_k(row['AmountNum']), fontsize=8, color=row['Color'], ha='left', va='bottom')
            ax.set_xlabel('Date')
            ax.set_ylabel('Price')
            ax.set_title('ETH Trades (Last 24 Months)')
            plt.xticks(rotation=45)
            st.pyplot(fig, use_container_width=True)


if __name__ == "__main__":
    main()
