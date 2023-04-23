from dotenv import load_dotenv
from os import environ
import logging
from bot import start_bot
from publisher import Publisher

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    load_dotenv()
    token = environ.get("TL_TOKEN")
    if token is None:
        logging.fatal("could not load telegram token")

    broker_host = environ.get("MQTT_HOST")
    broker_port = environ.get("MQTT_PORT")
    if broker_port is None:
        broker_port = 1883

    with Publisher(broker_host, broker_port) as publisher:
        start_bot(token=token)

if __name__ == '__main__':
    main()