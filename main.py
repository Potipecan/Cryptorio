import time, threading, os, csv, argparse

from typing_extensions import Literal
from typing import Callable

from io_interfaces.kafka_interface import KafkaInterface
from helpers.data_aggregator import CryptoDataAggregator
from logging import getLogger
from helpers.binance_price import get_best_prices
import keras

logger = getLogger(__name__)
symbol = None # cryptocurrency 
kafka_interface = KafkaInterface()
lstm_predictor: keras.models.Sequential | None = None
aggregator = CryptoDataAggregator(24 * 20)

data_output_file: None | str = None
predict_interval = 3600 # 1h interval between predictions
price_poll_interval = 600
mode: Literal['gather', 'predict'] = 'gather'

def handle_sentiment_input(value):
    for v in value:
        scores = v['analysis']['crypto_scores']
        if symbol in scores:
            aggregator.add_crypto_sentiment(scores[symbol])

topic_handler_map = {
    "sentiments": handle_sentiment_input,
    # "stocks:": handle_stocks_input,
}
   
def poll(func: Callable[[], None], interval: float):
    def _poll_exec():
        next_call = time.time()
        while True:
            func()    
            next_call += interval
            time.sleep(next_call - time.time())
            
    thread = threading.Thread(target=_poll_exec, daemon=True)
    thread.start()

def poll_price():
    if not kafka_interface.can_produce():
        logger.info("Can't poll prices, Kafka producer not connected!")
    else:
        price = get_best_prices(symbol)
        aggregator.add_crypto_price(price)

def predict():
    aggregator.aggregate()
    
    if mode == "gather":
        with open(data_output_file, "w+") as output_csv:
            writer = csv.writer(output_csv, sep=";")
            writer.writerow([time.time(), *aggregator.history_to_input_stream().flatten().tolist()[-1]]) # write latest data to csv
    elif mode == "predict":
        prediction = lstm_predictor.predict(aggregator.history_to_input_stream())
        
    else:
        raise ValueError("Invalid mode")
        

def kafka_message_callback(message):
    # handle incoming messages
    
    handler = topic_handler_map.get(message.topic, None)
    if handler is None:
        logger.warning("No handler for topic '%s'", message.topic)
        return
    
    handler(message.value)
    
    pass

def main():
    global symbol, data_output_file, price_poll_interval, mode, predict_interval, lstm_predictor
    parser = argparse.ArgumentParser("main.py")
    KafkaInterface.add_arguments_to_parser(parser)
    parser.add_argument("symbol", type=str)
    parser.add_argument("-M", "--mode", type=str, choices=['predict', 'gather'])
    parser.add_argument("--gather-output", type=str)
    parser.add_argument("--model", type=str)
    parser.add_argument('--price-poll-interval', type=float, default=600)
    parser.add_argument("--aggregation-interval", type=float, default=3600)
        
    args = parser.parse_args()
    
    price_poll_interval = args.price_poll_interval
    predict_interval = args.aggregation_interval
    mode = args.mode
    if mode == 'predict':
        if args.model is None:
            raise ValueError("Must specify a model in 'predict' mode")
        lstm_predictor = keras.models.load_model(args.model)
        
    elif mode == 'gather':
        if args.gather_output is None:
            raise ValueError("Must specify a gather output in 'gather' mode")
        data_output_file = os.path.abspath(args.gather_output)
        with open(data_output_file, "w") as f:
            writer = csv.writer(f, sep=";")
            writer.writerow([predict_interval, price_poll_interval])
        
    
    symbol = args.symbol
    kafka_interface.set_consumer_callback(kafka_message_callback)
    kafka_interface.start(args)
    
    poll(poll_price, price_poll_interval)
    poll(predict, predict_interval)
    
    pass

if __name__ == '__main__':
    main()