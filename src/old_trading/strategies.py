import pandas_ta as ta
from abc import abstractmethod, ABC


class StrategyFactory:
    @staticmethod
    def get_strategy(strategy_name, prices_history, **kwargs):
        if strategy_name == "Dummy":
            return DummyStrategy(prices_history)
        elif strategy_name == "RSI":
            return RSI(prices_history, **kwargs)
        elif strategy_name == "BollingerBands":
            return BollingerBands(prices_history, **kwargs)
        elif strategy_name == "MACD":
            return MACD(prices_history, **kwargs)
        elif strategy_name == "Stochastic":
            return Stochastic(prices_history, **kwargs)
        elif strategy_name == "ParabolicSAR":
            return ParabolicSAR(prices_history, **kwargs)
        else:
            raise ValueError("Invalid strategy name")


class Strategy(ABC):
    """
    Strategy class

    Attributes:
        signals: list of values in {-1, 0, 1} with length prices_history.shape[0]
        prices_history: pandas dataframe with original columns + strategy-specific columns
    """
    def __init__(self, prices_history):
        self.signals = None
        self.prices_history = prices_history.copy()
        self.prices_history["signal"] = 0

    @abstractmethod
    def generate_signal(self):
        """
        Generate signals: buy, sell or hold for each timestamp
        1 means buy, -1 means sell, 0 means hold

        Returns:
            list of values in {-1, 0, 1} as long as prices_history.shape[0]
        """
        pass


class DummyStrategy(Strategy):
    """
    Dummy strategy
    """
    def generate_signal(self):
        self.prices_history["signal"] = [0] * self.prices_history.shape[0]

        return self.prices_history.signal


class RSI(Strategy):
    """
    RSI strategy
    """
    def __init__(self, prices_history, window, rsi_threshold_buy, rsi_threshold_sell):
        super().__init__(prices_history)
        self.window = window
        self.rsi_threshold_buy = rsi_threshold_buy
        self.rsi_threshold_sell = rsi_threshold_sell

    def _compute_rsi(self):
        self.prices_history['RSI'] = ta.rsi(self.prices_history.price, self.window)

    def generate_signal(self):
        self._compute_rsi()

        self.prices_history.loc[self.prices_history["RSI"] < self.rsi_threshold_buy, "signal"] = 1
        self.prices_history.loc[self.prices_history["RSI"] > self.rsi_threshold_sell, "signal"] = -1

        return self.prices_history.signal


class BollingerBands(Strategy):
    """
    Bollinger Bands strategy
    """
    def __init__(self, prices_history, window, num_std_dev):
        super().__init__(prices_history)
        self.window = window
        self.num_std_dev = float(num_std_dev)

    def _compute_bollinger_bands(self):
        bbands = ta.bbands(self.prices_history.price, self.window, self.num_std_dev)
        self.prices_history["BBL"] = bbands[f"BBL_{self.window}_{self.num_std_dev}"]
        self.prices_history["BBU"] = bbands[f"BBU_{self.window}_{self.num_std_dev}"]

    def generate_signal(self):
        self._compute_bollinger_bands()

        self.prices_history.loc[self.prices_history["price"] < self.prices_history["BBL"], "signal"] = 1
        self.prices_history.loc[self.prices_history["price"] > self.prices_history["BBU"], "signal"] = -1

        return self.prices_history.signal


class ParabolicSAR(Strategy):
    """
    Parabolic SAR strategy
    """
    def __init__(self, prices_history, acceleration, acceleration_max):
        super().__init__(prices_history)
        self.acceleration = acceleration
        self.acceleration_max = acceleration_max

    def _compute_parabolic_sar(self):
        psar = ta.psar(self.prices_history.high, self.prices_history.low, af=self.acceleration, max_af=self.acceleration_max)
        self.prices_history["PSARl"] = psar[f"PSARl_{self.acceleration}_{self.acceleration_max}"]
        self.prices_history["PSARs"] = psar[f"PSARs_{self.acceleration}_{self.acceleration_max}"]

    def generate_signal(self):
        self._compute_parabolic_sar()

        self.prices_history.loc[self.prices_history["price"] < self.prices_history["PSARl"], "signal"] = 1
        self.prices_history.loc[self.prices_history["price"] > self.prices_history["PSARs"], "signal"] = -1

        return self.prices_history.signal
