import csv, argparse
from keras.api.layers import LSTM, Dense
from keras.api.models import Sequential


lookback = 5 * 24
lstm_layers = 16
lookahead = 1 * 24

    
def train(dataset, output_filename):
    with open(dataset, "r") as f:
        reader = csv.reader(f)
        settings = [float(x) for x in next(reader)]
        
        datapoints = []
        for line in reader:
            datapoints.append([float(x) for x in line[1:]])
        
        data_x = [datapoints[x: x + lookback, : 3] for x in range(len(datapoints) - lookback - lookahead + 1)]
        data_y = [y[3:] for y in datapoints[lookback + lookahead - 1:]]
    
    model = Sequential()
    model.add(LSTM(32, activation='tanh', input_shape=(lookback, 3)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    history = model.fit(data_x, data_y, epochs=100, batch_size=32)
    
    model.save(output_filename)
        

def main():
    parser = argparse.ArgumentParser()
    pass


if __name__ == '__main__':
    main()
    