import pandas as pd
import streamlit as st
import time
import matplotlib.pyplot as plt

from src.config import WHITELISTED_ASSETS, asset_to_step
from src.kraken import KrakenAPI, Kraken
from src.utils import load_keys, round_sig_dict


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


def reset_trading_volumes(asset=None):
    if asset:
        st.session_state[f"asset_volume_{asset}"] = 0
        st.session_state[f"usd_volume_{asset}"] = 0
    else:
        # Reset all assets
        for asset in ["XXBT", "XETH"]:
            st.session_state[f"asset_volume_{asset}"] = 0
            st.session_state[f"usd_volume_{asset}"] = 0


def update_asset_volume(asset_price, asset):
    st.session_state[f"asset_volume_{asset}"] = st.session_state[f"usd_volume_{asset}"] / asset_price


def update_usd_volume(asset_price, asset):
    st.session_state[f"usd_volume_{asset}"] = st.session_state[f"asset_volume_{asset}"] * asset_price


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
    cutoff = now - pd.DateOffset(months=12)  # Last year instead of 24 months

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

        date = trade_time.strftime('%-d %b %Y')
        buy_sell = 'BUY' if trade['type'].lower() == 'buy' else 'SELL'

        # Amount in USD (cost), round to -1 decimals, with dollar sign
        try:
            amount_usd = f"${round(float(trade.get('cost', 0)), -1):,.0f}"
        except (ValueError, TypeError):
            amount_usd = "$0"
        # Price, round based on asset type: BTC to -2, ETH to -1
        try:
            if asset_filter == 'BTC':
                price = round(float(trade.get('price', 0)), -2)  # Round to nearest 100
            else:  # ETH
                price = round(float(trade.get('price', 0)), -1)  # Round to nearest 10
        except (ValueError, TypeError):
            price = 0.0
        rows.append({
            'Date': date,
            'Type': buy_sell,
            'Price': price,
            'Amount $': amount_usd,
        })
    df = pd.DataFrame(rows)
    return df  # Return all trades from last year, not limited to 10


def styled_trade_table(df):
    def highlight_type(val):
        return 'background-color: #d4f8e8' if val == 'BUY' else 'background-color: #ffd6d6'
    # Only paint Type column, do not touch Price
    return df.style.apply(lambda col: [highlight_type(v) for v in col], subset=['Type']).format({'Price': '{:.0f}'})


def trade_scatter_plot(df, asset_name):
    df['Timestamp'] = pd.to_datetime(df['Date'], format='%d %b %Y')
    df['AmountNum'] = df['Amount $'].str.replace(r'[$,]', '', regex=True).astype(float)
    df['Color'] = df['Type'].map({'BUY': 'green', 'SELL': 'red'})
    def format_k(amount):
        if amount >= 1000:
            return f"{amount/1000:.1f}k"
        else:
            return f"{int(amount)}"
    fig, ax = plt.subplots()
    ax.plot(df['Timestamp'], df['Price'].astype(float), color='gray', linestyle='-', linewidth=1, zorder=1)
    for idx, row in df.iterrows():
        ax.scatter(row['Timestamp'], float(row['Price']), s=row['AmountNum']/df['AmountNum'].max()*100+20, color=row['Color'], zorder=2)
        # Position text farther from circle to avoid overlap
        price_range = df['Price'].max() - df['Price'].min()
        offset = price_range * 0.03  # 3% of price range as offset
        ax.text(row['Timestamp'], float(row['Price']) + offset, format_k(row['AmountNum']), fontsize=8, color='black', ha='left', va='bottom')
    
    # Add today's price point
    today = pd.Timestamp('now').normalize()
    asset_key = 'XXBT' if asset_name == 'BTC' else 'XETH'
    current_price = st.session_state.prices.get(asset_key, 0)
    if current_price > 0:
        ax.scatter(today, current_price, s=100, color='gray', zorder=3, alpha=0.7)
        # Position text farther from circle and in black
        price_range = df['Price'].max() - df['Price'].min()
        offset = price_range * 0.05  # 5% of price range as offset
        ax.text(today, current_price + offset, 'Today', fontsize=8, color='black', ha='center', va='bottom')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.set_title(f'{asset_name} Trades (Last Year)')
    plt.xticks(rotation=45)
    return fig


def main():
    set_page_config()
    load_info()

    st.button("UPDATE", on_click=update_info)

    with st.columns([1, 2])[0]:
        balances_info = [{"asset": asset, "volume": volume, "volume_USD": st.session_state.balances_usd[asset]} for asset, volume in st.session_state.balances.items()]
        balances_df = pd.DataFrame(balances_info)

        balances_df.sort_values("volume_USD", ascending=False, inplace=True)
        balances_df.set_index("asset", inplace=True)

        balance_total = balances_df["volume_USD"].sum()

        st.header(f"My Balance: {round(balance_total)}$")
        st.dataframe(balances_df)

    st.markdown("---")


    col_btc, col_eth = st.columns(2, gap="large", border=True)

    with col_btc:
        ui_trade_asset("XXBT")

        ui_last_trades("BTC")
            
    with col_eth:
        ui_trade_asset("XETH")

        ui_last_trades("ETH")


def ui_last_trades(asset):
    """
    Display the latest trades for a given asset.
    
    Args:
        asset (str): Asset name in user-friendly format ("BTC" or "ETH")
    """
    st.subheader(f"Latest {asset} Orders")
    last_trades_df = get_last_trades(asset_filter=asset)
    # st.dataframe(styled_trade_table(last_trades_df), use_container_width=True, hide_index=True)
    if not last_trades_df.empty:
        fig = trade_scatter_plot(last_trades_df, asset)
        st.pyplot(fig, use_container_width=True)


def ui_trade_asset(asset):
    asset_price = st.session_state.prices.get(asset)
    st.header(asset)
    st.subheader(f"Price: {asset_price}$")

    col1, col2, _, _ = st.columns(4)
    with col1:
        volume_usd = st.number_input("USD", step=asset_to_step["ZUSD"], key=f"usd_volume_{asset}", on_change=update_asset_volume, kwargs={"asset_price": asset_price, "asset": asset})
    with col2:
        volume_asset = st.number_input(asset, step=asset_to_step[asset], key=f"asset_volume_{asset}", on_change=update_usd_volume, kwargs={"asset_price": asset_price, "asset": asset}, format="%.5f")

    with col1:
        if st.button(f"BUY {asset}"):
            if volume_usd > st.session_state.balances["ZUSD"]:
                st.error("Not enough USD funds")
            else:
                if kraken.buy_market(asset, volume_asset):
                    confirm_trade()
                else:
                    st.error("Something went wrong")
    with col2:
        if st.button(f"SELL {asset}"):
            if volume_asset > st.session_state.balances[asset]:
                st.error(f"Not enough {asset} funds")
            else:
                if kraken.sell_market(asset, volume_asset):
                    confirm_trade()
                else:
                    st.error("Something went wrong")


if __name__ == "__main__":
    main()
