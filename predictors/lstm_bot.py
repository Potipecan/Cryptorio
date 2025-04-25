import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import time
import datetime
from dateutil import parser
import matplotlib.dates as mdates
import matplotlib.ticker as plticker

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error

import keras


lookback = 20
lstm_layers = 16


class CryptoDataPoint:
    def __init__(self):
        self.timestamp = None
        self.sentiment = None
        self.value = None


class lstm_predictor():
    def __init__(self):
        self.cryptos : dict[str, list[CryptoDataPoint]] = {}
        self.model = None
        self.init_model()
        
    def init_model(self):
        self.model = keras.models.Sequential()
        self.model.add(keras.layers.LSTM(lstm_layers, input_shape=(lookback, 1))) # TODO: get proper shape once you figure out how the data is actually gonna look like
        
    def push_data_point(self, cr_id: str, data: CryptoDataPoint):
        if cr_id not in self.cryptos:
            self.cryptos[cr_id] = []
        self.cryptos[cr_id].append(data)
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=lookback)
        d_list = [i for i in self.cryptos[cr_id] if i.timestamp > cutoff_date]
        d_list.sort()
        for _ in range(0, len(d_list) - lookback): # erase old data
            d_list.pop(0)
        self.cryptos[cr_id] = d_list
        
    def reevaluate(self):
        pass