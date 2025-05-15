import kafka
import kafka.errors as k_errors
import argparse
import os
import signal
import threading
from logging import log
import logging
from typing import Callable
import json


class KafkaInterface:
    def __init__(self):
        self.input_topics: list[str] = []
        self.output_topic: str | None = None
        self.producer: kafka.KafkaProducer | None = None
        self.consumer: kafka.KafkaConsumer | None = None
        self.consumer_thread: threading.Thread | None = None
        self.consumer_stop_event = threading.Event()
        self.on_message_received: Callable[[any], None] | None = None

    @staticmethod
    def add_arguments_to_parser(parser: argparse.ArgumentParser):
        parser.add_argument("--kafka-client-id", type=str,
                            default=os.environ.get("AGENT_KAFKA_CLIENT_ID", "kafka_interface"))
        parser.add_argument("--kafka-broker-address", type=str,
                            default=os.environ.get("AGENT_KAFKA_BROKER_ADDRESS", "localhost"))
        parser.add_argument("--kafka-broker-port", type=int,
                            default=int(os.environ.get("AGENT_KAFKA_BROKER_PORT", 9092)))
        parser.add_argument("-i", "--kafka-input-topic", type=str, nargs="+", required=False)

    def init_kafka_producer(self, client_id: str, server: str, port: int) -> bool:
        log(logging.INFO, f"Initializing the Kafka producer with bootstrap server {server}:{port}.")
        try:
            self.producer = kafka.KafkaProducer(bootstrap_servers=f"{server}:{port}",
                                                client_id=client_id + "_producer",
                                                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"))
        except k_errors.KafkaError as e:
            log(logging.ERROR, "Failed to initialize Kafka producer, reason: %s", e)
            return False
        return True

    def init_kafka_consumer(self, client_id: str, server: str, port: int) -> bool:
        log(logging.INFO, f"Initializing the Kafka consumer with bootstrap server {server}:{port}. "
                          f"Subscribing to topics: {self.input_topics}")
        try:
            self.consumer = kafka.KafkaConsumer(*self.input_topics,
                                                bootstrap_servers=f"{server}:{port}",
                                                group_id=client_id,
                                                client_id=client_id + "_consumer",
                                                consumer_timeout_ms=1000,
                                                auto_offset_reset="earliest",
                                                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
                                                )
        except k_errors.KafkaError as e:
            log(logging.ERROR, "Failed to initialize Kafka consumer, reason: %s", e)
            return False
        return True

    def set_consumer_callback(self, callback: Callable[[any], None]) -> None:
        self.on_message_received = callback

    def consumer_thread_work(self):
        if self.consumer is None:
            raise ValueError("Kafka consumer is not initialized.")
        self.consumer.poll(1000)
        log(logging.INFO, "Kafka polling started")
        while not self.consumer_stop_event.is_set():
            for record in self.consumer:
                if self.on_message_received is not None:
                    self.on_message_received(record)

                if self.consumer_stop_event.is_set():
                    break
        pass

    def start(self, args, has_output: bool = True):
        self.input_topics = args.kafka_input_topic
        if len(self.input_topics) > 0:
            self.init_kafka_consumer(args.kafka_client_id, args.kafka_broker_address, args.kafka_broker_port)
            self.consumer_thread = threading.Thread(target=self.consumer_thread_work, daemon=True)
            self.consumer_thread.start()

        if has_output is not None:
            self.init_kafka_producer(args.kafka_client_id, args.kafka_broker_address, args.kafka_broker_port)

    def stop(self):
        self.consumer_stop_event.set()
        if self.can_produce():
            self.producer.close()
            log(logging.INFO, "Kafka producer connection closed")
        if self.can_consume():
            self.consumer.close()
            log(logging.INFO, "Kafka consumer connection closed")

    def send_message(self, topic: str, message: bytes | dict):
        assert self.producer is not None
        if isinstance(message, dict):
            message = json.dumps(message).encode()

        assert isinstance(message, bytes)

        future = self.producer.send(topic, message)
        try:
            print(future.get(timeout=10))
        except Exception as ex:
            print(ex)

    def can_produce(self):
        return self.producer is not None and self.producer.bootstrap_connected()

    def can_consume(self):
        return self.consumer is not None and self.consumer.bootstrap_connected()


def int_signal_handler(sig, _):
    if sig == signal.SIGINT:
        client.stop()


def response_handling(record):
    print(record)
    client.send_message("pong", record.value)


def main():
    signal.signal(signal.SIGINT, int_signal_handler)

    parser = argparse.ArgumentParser()
    client.add_arguments_to_parser(parser)
    client.set_consumer_callback(response_handling)
    args = parser.parse_args()
    client.start(args)


if __name__ == '__main__':
    client = KafkaInterface()
    main()
