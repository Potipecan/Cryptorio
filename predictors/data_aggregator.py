import datetime
import json
import numpy as np


class HistoricData:
    def __init__(self):
        self.best_bid_high = 0
        self.best_bid_avg = 0
        self.best_ask_low = 0
        self.best_ask_avg = 0
        self.sentiment_high = 0
        self.sentiment_low = 0
        self.sentiment_avg = 0
        self.sentiment_vol = 0
        self.timestamp = datetime.datetime.now()

    def __dict__(self):
        return {
            'best_bid_high': self.best_bid_high,
            'best_bid_avg': self.best_bid_avg,
            'best_ask_low': self.best_ask_low,
            'best_ask_avg': self.best_ask_avg,
            'sentiment_high': self.sentiment_high,
            'sentiment_low': self.sentiment_low,
            'sentiment_avg': self.sentiment_avg,
            'sentiment_vol': self.sentiment_vol,
            'timestamp': self.timestamp
        }


class CryptoDataAggregator(object):
    def __init__(self, n):
        self.n = n
        self.history = []
        self.current_interval_sentiments = []
        self.current_interval_prices = []
        self.export_file = None

    def add_crypto_sentiment(self, crypto_sentiment: float):
        self.current_interval_sentiments.append(crypto_sentiment)

    def add_crypto_price(self, crypto_price: float):
        self.current_interval_prices.append(crypto_price)

    def aggregate(self):
        d = HistoricData()
        d.sentiment_high = max(self.current_interval_sentiments)
        d.sentiment_low = min(self.current_interval_sentiments)
        d.sentiment_avg = sum(self.current_interval_sentiments) / len(self.current_interval_sentiments)
        d.sentiment_vol = len(self.current_interval_sentiments)
        d.best_bid_high = max(self.current_interval_prices[:, 0])
        d.best_bid_avg = min(self.current_interval_sentiments[:, 0]) / len(self.current_interval_prices)
        d.best_ask_low = min(self.current_interval_prices[:, 1])
        d.ave_ask_low = sum(self.current_interval_prices[:, 1]) / len(self.current_interval_prices)

        self.current_interval_sentiments.clear()
        self.current_interval_prices.clear()

        self.history.append(d)
        if len(self.history) > self.n:
            self.history.pop(0)

        if self.export_file is not None:
            with open(self.export_file, "a") as f:
                json.dump(d.__dict__(), f)
                f.write("\n")

    def history_to_input_stream(self):
        arr = np.array([[d.best_bid_high, d.best_bid_avg, d.best_ask_low, d.best_ask_avg, d.sentiment_high,
                         d.sentiment_low, d.sentiment_avg, ] for d in self.history])
        
        if len(arr) < self.n:
            np.pad(arr, ((self.n - len(arr), 0), (0, 0)), mode='constant', constant_values=0)
