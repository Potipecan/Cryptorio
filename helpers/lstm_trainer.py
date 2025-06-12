import csv, argparse

import sklearn.model_selection
from sklearn.preprocessing import MinMaxScaler
from keras.api.layers import LSTM, Dense, Input
from keras.api.models import Sequential
from datetime import datetime
from pandas import DataFrame
import numpy as np
from keras.api.callbacks import EarlyStopping
import matplotlib.pyplot as plt

samps_per_day = 1
lookback = 7 * samps_per_day
lookahead = 1 * samps_per_day

    
def train(dataset, output_filename):
    scaler = MinMaxScaler(feature_range=(0, 1))

    with open(dataset, "r") as f:
        reader = csv.reader(f)
        settings = [float(x) for x in next(reader)]
        
        datapoints = np.array(list(map(lambda x: (datetime.fromisoformat(x[0]), float(x[1]), float(x[2]), float(x[3])), reader)))
        datapoints[:, 2:] = scaler.fit_transform(datapoints[:, 2:])
        
        data_x = np.array([datapoints[x: x + lookback, 1: ] for x in range(len(datapoints) - lookback - lookahead + 1)], dtype=np.float32)
        data_y = np.array([y[2:] for y in datapoints[lookback + lookahead - 1:]], dtype=np.float32)
        dates_y = np.array([y[0] for y in datapoints[lookback + lookahead - 1:]])
    
    train_x, test_x, train_y, test_y, _, dates_y = sklearn.model_selection.train_test_split(data_x, data_y, dates_y, test_size=0.1, shuffle = False)
    test_y = scaler.inverse_transform(test_y)
    
    model = Sequential()
    model.add(Input(shape=(lookback, 3)))
    model.add(LSTM(128, activation='tanh'))
    model.add(Dense(2, activation='sigmoid'))
    model.compile(optimizer='adam', loss='mse')
    history = model.fit(train_x, train_y,
                        epochs=25, 
                        batch_size=32, 
                        validation_split=0.2,
                        # shuffle=False,
                        callbacks=[EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)]
                        )
    history_df = DataFrame(history.history)
    
    model.save(f'{output_filename}.keras')
    history_df.to_json(f'{output_filename}.history.json')
    
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    plt.plot(np.arange(1, len(loss) + 1), loss, label='train')
    plt.plot(np.arange(1, len(val_loss) + 1), val_loss, label='validate')
    plt.legend()
    plt.show()
    
    pred_y = model.predict(test_x, batch_size=test_x.shape[0])
    pred_y = scaler.inverse_transform(pred_y)

    plt.plot(dates_y, test_y[:, 0], label='dejanski_višek')
    plt.plot(dates_y, test_y[:, 1], label='dejansko_dno')  
    plt.plot(dates_y, pred_y[:, 0], label='predvideni_višek')
    plt.plot(dates_y, pred_y[:, 1], label='predvideno_dno')
    plt.xticks(None, None, rotation=90)
    plt.title("Predvidevanja cene za Bitcoin")
    plt.ylabel("Cena [$]")
    plt.xlabel("Datum")
    plt.legend()
    plt.tight_layout()
    plt.show()
        

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument('output')
    args = parser.parse_args()
    
    train(args.dataset, args.output)


if __name__ == '__main__':
    main()
    