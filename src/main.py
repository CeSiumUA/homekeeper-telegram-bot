from env import Env
import logging
from tlbot import TlBot
from publisher import Publisher

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    
    if Env.load_required_values():
        logging.info('env verified')
    else:
        logging.fatal('not enough variable set')

    broker_host, broker_port, broker_username, broker_password = Env.get_mqtt_connection_params()

    bot = TlBot(token=Env.get_tl_token(), chat_id=Env.get_tl_chat_id())
    with Publisher(broker_host, broker_port, bot.send_message, broker_username=broker_username, broker_password=broker_password) as publisher:
        bot.start_bot(publish_callback=publisher.publish)

if __name__ == '__main__':
    main()