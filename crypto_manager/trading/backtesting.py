def backtest(price_history, signals, initial_balance=10000):
    """
    Simple backtest function to compute strategy performance.

    Args:
    - price_history: DataFrame with historical price data.
    - signals: Series or list of {-1, 0, 1} values. 1 for buy, -1 for sell, 0 for hold.
    - initial_balance: starting balance in your trading account.

    Returns:
    - A dictionary with final_balance, total_profit/loss, and trade count.
    """

    balance = initial_balance
    position = 0
    trade_count = 0

    # Assume the price_history is in the same order as signals and has a "price" column
    for price, signal in zip(price_history["price"], signals):
        if signal == 1:  # Buy
            position += balance / price
            balance = 0
            trade_count += 1

        elif signal == -1:  # Sell
            balance += position * price
            position = 0
            trade_count += 1

    # Calculate the final balance, assuming we sell any position at the end
    balance = position * price if position > 0 else balance

    return {
        "final_balance": round(balance),
        "profit_or_loss": balance - initial_balance,
        "profit_or_loss_percent": round((balance - initial_balance) / initial_balance * 100, 2),
        "trade_count": trade_count
    }


#
# class Backtester:
#     def __init__(self, strategy, initial_money):
#         self.strategy = strategy
#         self.initial_money = initial_money
#         self.initial_asset = 0
#
#         self.current_money = self.initial_money
#         self.current_asset = self.initial_asset
#
#         self.prices_history_df = self.strategy.generate_signal()
#
#     def buy(self, price):
#         self.current_asset = self.current_money / price
#         self.current_money = 0
#
#     def sell(self, price):
#         self.current_money = self.current_asset * price
#         self.current_asset = 0
#
#     def backtest(self):
#         for index, row in self.prices_history_df.iterrows():
#             if row.signal == 1 and self.current_money > 0:
#                 self.buy(row.price)
#             elif row.signal == -1 and self.current_asset > 0:
#                 self.sell(row.price)
#             else:
#                 pass
#
#             self.prices_history_df.loc[index, "money"] = self.current_money
#             self.prices_history_df.loc[index, "asset"] = self.current_asset
#             self.prices_history_df.loc[index, "total"] = self.current_money + self.current_asset * row.price
#
#         return self.prices_history_df
#
#     def backtest_performance(self):
#         self.backtest()
#         return self.prices_history_df.iloc[-1].total - self.initial_money
#
#     def backtest_performance_percentage(self):
#         return self.backtest_performance() / self.initial_money * 100
