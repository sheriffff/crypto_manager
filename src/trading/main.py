import json

from src.kraken import initialize_kraken_api
from src.trading.backtesting import backtest
from src.trading.strategies import RSI, BollingerBands, StrategyFactory
from src.trading.utils import load_config

data_handler = initialize_kraken_api()
config = load_config()
prices_history = data_handler.get_prices_history(config["general"]["pair"], config["general"]["interval_mins"])

for strategy_name, strategy_params in config["strategies"].items():
    strategy = StrategyFactory.get_strategy(strategy_name, prices_history, **strategy_params)
    strategy_signals = strategy.generate_signal()
    strategy_results = backtest(prices_history, strategy_signals)
    print(strategy_name, json.dumps(strategy_results, indent=4))


# signals_table = pd.crosstab(rsi_signals, bollinger_signals, rownames=["RSI"], colnames=["Bollinger Bands"])

