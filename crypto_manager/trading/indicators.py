def calculate_bollinger_bands(df, window, num_std_dev):
    rolling_mean = df['price'].rolling(window).mean()
    rolling_std_dev = df['price'].rolling(window).std()

    # Calculamos las Bandas de Bollinger
    df['BB_upper'] = rolling_mean + num_std_dev * rolling_std_dev
    df['BB_lower'] = rolling_mean - num_std_dev * rolling_std_dev

    return df


def should_buy(df):
    last_row = df.iloc[-1]

    # RSI < 30 means oversold, so we should buy
    # price < BB_lower means price is below the lower band, so we should buy
    return last_row['RSI'] < 30 and last_row['price'] < last_row['BB_lower']


def should_sell(df):
    last_row = df.iloc[-1]

    # RSI > 70 means overbought, so we should sell
    # price > BB_upper means price is above the upper band, so we should sell
    return last_row['RSI'] > 70 or last_row['price'] > last_row['BB_upper']
