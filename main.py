from data_handling import data_handler, strategy, backtester


def main():
    data = data_handler("AAPL", start_date="2026-01-01", end_date = "2026-05-05").load_data()

    strat = strategy(
    indicators={"sma_10": lambda df: df["close"].rolling(window=5).mean(), 
                "sma_100": lambda df: df["close"].rolling(window=40).mean(),
                },
    signal_logic=(lambda df: 1 if df["sma_10"] > df["sma_100"] else -1)
    )
    data = strat.calculate_signals(data)
    print(data.tail(n=50))
    Backtester = backtester()
    myDict = {"one asset": data}
    Backtester.backtest(myDict)
    #ReceivedData = Backtester.backtest(myDict)
    #print(ReceivedData["data"].tail(n=50))
    #print(ReceivedData["history"].tail(n=50))
    Backtester._print_portfolio()
    Backtester.calculate_metrics()
if __name__ == '__main__':
    main()
