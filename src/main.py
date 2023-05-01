from dotenv import load_dotenv
from os import environ
import logging
from tlbot import TlBot
from publisher import Publisher

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    load_dotenv()
    token = environ.get("TL_TOKEN")
    if token is None:
        logging.fatal("could not load telegram token")

    chat_id = environ.get("CHAT_ID")
    if chat_id is None:
        logging.fatal("could not load chat id")
    else:
        chat_id = int(chat_id)

    broker_host = environ.get("MQTT_HOST")
    if broker_host is None:
        logging.fatal("could not load mqtt host")
    else:
        logging.info("MQTT host: %s", broker_host)
    broker_port = environ.get("MQTT_PORT")
    if broker_port is None:
        broker_port = 1883
    else:
        broker_port = int(broker_port)
    logging.info("MQTT port: %d", broker_port)

    bot = TlBot(token=token, chat_id=chat_id)
    with Publisher(broker_host, broker_port, bot.send_message) as publisher:
        bot.start_bot(publish_callback=publisher.publish)

if __name__ == '__main__':
    main()