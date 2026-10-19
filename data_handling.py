from typing import Optional
import pandas as pd
from openbb import obb


class data_handler:
    def __init__(self, symbol: str, start_date: Optional[str] = "2026-10-14", end_date: Optional[str] = None, provider: str = "cboe"):
        self.symbol = symbol.upper()
        self.start_date = start_date
        self.end_date = end_date
        self.provider = provider


    def load_data(self) -> pd.DataFrame | dict[str, pd.DataFrame]:
        data = obb.equity.price.historical(symbol=self.symbol, start_date=self.start_date, end_date=self.end_date, provider=self.provider).to_df()

        if ',' in self.symbol:
            data = data.reset_index().set_index('symbol')
            return {sym: data.loc[sym] for sym in self.symbol.split(',')}
        return data

    def load_csv(self, path) -> pd.DataFrame:
        return pd.read_csv(path, index_col="date", parse_dates=["date"])


class strategy:
    def __init__(self, indicators: dict, signal_logic: Any):
        self.indicators = indicators
        self.signal_logic = signal_logic

    def calculate_signals(self, df: pd.DataFrame | List[pd.DataFrame]):
        if isinstance(df, dict):
            for a, b in df:
                self._apply_strategy_helper(self, b)
        else:
            self._apply_strategy_helper(self, df)
        return df


    def _apply_strategy_helper(self, df: pd.DataFrame): #generate signals
        for name, indicator_func in self.indicators:
            df[name] = indicator_func(df)
        df["signal"] = df.apply(lambda r: self.signal_logic(r), axis = 1) #axis 0 for cols, 1 for rows
        df["position"] = df["signal"].diff.fillna(0)  #only diff's matter cuz you only change if 0 -> 1
        return df


data = data_handler("AAPL").load_data()
strat = strategy(
    indicators={"sma_10", lambda df: df["close"].rolling(window=10).mean(), 
                "sma_100", lambda df: df["close"].rolling(window=100).mean(),
                },
    signal_logic=(lambda df: 1 if df["sma_10"] > df["sma_100"] else -1)
    )
print(data.head())
