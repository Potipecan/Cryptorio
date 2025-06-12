from csv import reader, writer
from datetime import datetime
import numpy as np
import argparse
import pytz

def merge_datasets(prices, sentiments, output):
    with open(prices, 'r') as pf:
        with open(sentiments, 'r') as sf:
            sent_reader = reader(sf, delimiter=',')
            price_reader = reader(pf, delimiter=';')
            next(sent_reader)
            next(price_reader)
            sentiments = np.array(list(map(lambda x: (datetime.fromisoformat(x[0]).replace(tzinfo=pytz.UTC), float(x[2])), sent_reader)))
            
            with open(output, 'w') as of:
                output_writer = writer(of)
                output_writer.writerow([])
                for pr in price_reader:
                    date_open = datetime.fromisoformat(pr[0])
                    date_close = datetime.fromisoformat(pr[1])
                    
                    high = float(pr[6])
                    low = float(pr[7])
                    valid_sent = sentiments[np.where((sentiments[:, 0] >= date_open) & (sentiments[:, 0] <= date_close))[0], 1]
                    sent = np.mean(valid_sent) if len(valid_sent) > 0 else 0
                    
                    output_writer.writerow([date_open, sent, high, low])
                    
     
def main():
    # parser = argparse.ArgumentParser('prep')
    # parser.add_argument("sent_file")
    # parser.add_argument("price_file")
    # parser.add_argument("output_file")
    # args = parser.parse_args()
    
    # merge_datasets(args.sent_file, args.price_file, args.output_file)
    merge_datasets('prices.csv', 'bitcoin_sentiments_21_24.csv', 'btc_price_sentiments.csv')
    
if __name__ == '__main__':
    main()