from typing import Optional
import pandas as pd
from openbb import obb
import matplotlib.pyplot as plt

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

    def calculate_signals(self, df: pd.DataFrame | dict[str, pd.DataFrame]):
        if isinstance(df, dict):
            for a, b in df.items():
                self._apply_strategy_helper(b)
        else:
            self._apply_strategy_helper(df)
        return df


    def _apply_strategy_helper(self, df: pd.DataFrame): #generate signals
        for name, indicator_func in self.indicators.items():
            df[name] = indicator_func(df)
        df["signal"] = df.apply(lambda r: self.signal_logic(r), axis = 1) #axis 0 for cols, 1 for rows
        df["position"] = df["signal"].diff().fillna(0)  #only diff's matter cuz you only change if 0 -> 1

        return df


class backtester:
    def __init__(self, initial_capital: float = 10000, commission_pct: float = 0.001, commission_fixed: float = 1.0, plot: bool = True):
        self.plot = plot
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.commission_fixed = commission_fixed
        self.asset_data: dict = {}
        self.portfolio_history: dict = {}
        self.total_portfolio_history: list = []

    def _execute_trade(self, asset: str, action: int, price: float):
        if action > 0 and self.asset_data[asset]["cash"] > 0:
            value = self.asset_data[asset]["cash"]
            shares = (value - self._calc_fee(value)) / price
            self.asset_data[asset]["position"] += shares
            self.asset_data[asset]["cash"] -= value
            print("BOUGHT")
        if action < 0 and self.asset_data[asset]["position"] > 0:
            shares_to_sell = self.asset_data[asset]["position"]
            revenue = shares_to_sell * price + self._calc_fee(shares_to_sell * price)
            self.asset_data[asset]["cash"] += revenue
            self.asset_data[asset]["position"] -= shares_to_sell
            print("SOLD")

    def _calc_fee(self, amount_trading: float):
        return max(self.commission_fixed, self.commission_pct * amount_trading)

    def _update_portfolio(self, asset: str, price: float):
        self.asset_data[asset]["position_value"] = self.asset_data[asset]["position"] * price
        self.asset_data[asset]["total_value"] = self.asset_data[asset]["cash"] + self.asset_data[asset]["position_value"]
        self.portfolio_history[asset].append(self.asset_data[asset]["total_value"])

    def backtest(self, data: dict): #asset name, the dataframe for it
        asset_number = len(data)
        #ret = {}
        for asset_name in data:
            #ret[asset_name] = {}
           # ret[asset_name]["data"] = {}
            #ret[asset_name]["history"] = {}
            self.asset_data[asset_name] = {}
            self.portfolio_history[asset_name] = []
            for date, row in data[asset_name].iterrows():
                self.asset_data[asset_name]["cash"] = self.initial_capital / asset_number
                self.asset_data[asset_name]["position"] = 0
                self.asset_data[asset_name]["position_value"] = 0
                self.asset_data[asset_name]["total_value"] = 0 
                self._execute_trade(asset_name, row["signal"], row["close"])
                self._update_portfolio(asset_name, row["close"])
                if len(self.total_portfolio_history) < len(self.portfolio_history[asset_name]):
                    self.total_portfolio_history.append(self.asset_data[asset_name]["total_value"])
                else:
                    self.total_portfolio_history[-1] += self.asset_data[asset_name]["total_value"]
            
            #ret[asset_name]["data"] = self.asset_data[asset_name].to_df()
            #ret[asset_name]["history"] = self.portfolio_history[asset_name].to_df()
        #return ret
    def calculate_metrics(self):
        portfolio_values = pd.Series(self.total_portfolio_history)
        daily_returns = portfolio_values.pct_change().dropna()
        total_return = portfolio_values.iloc[-1] / self.initial_capital
        annualized_return = total_return / len(portfolio_values)
        #boring metrics copied off google
        #annualized_volatility = calculate_annualized_volatility(daily_returns)
        #sharpe_ratio = calculate_sharpe_ratio(annualized_return, annualized_volatility)
        #sortino_ratio = calculate_sortino_ratio(daily_returns, annualized_return)
        #max_drawdown = calculate_maximum_drawdown(portfolio_values)

        if self.plot:
            self._plot_metrics(portfolio_values, daily_returns)

    def _plot_metrics(self, portfolio_values: list, daily_returns: list):
        plt.figure(figsize=(10, 6))
        plt.subplot(2, 1, 1)
        plt.plot(portfolio_values, label="Portfolio Values")
        plt.title("Portfolio Value Over Time")
        plt.show()
    def _print_portfolio(self):
        for asset_name in self.portfolio_history:
            df = pd.DataFrame({"Portfolio": self.portfolio_history[asset_name]})
            #print(df[df["Portfolio"] != 10000.0].reset_index(drop=True))
            print(df[df["Portfolio"] != 10000.0])