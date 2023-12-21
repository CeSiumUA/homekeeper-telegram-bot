import random
import logging
import topics
from paho.mqtt.client import Client

class Publisher:
    def __init__(self, address: str, port: int, on_message, client_id: str | None = None, broker_username: str | None = None, broker_password: str | None = None) -> None:
        self.__address = address
        self.__port = port
        self.__broker_username = broker_username
        self.__broker_password = broker_password
        self.__client_id = client_id if client_id is not None else f'telegram-{random.randint(0, 1000)}'
        self.__msg_callback = on_message

    def publish(self, topic: str, message):
        res = self.__client.publish(topic=topic, payload=message, qos=2)
        if res.rc == 0:
            logging.info(f"sent message to `{topic}`")
        else:
            logging.error(f"failed to send message to `{topic}`, res: %d\n", res.rc)

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("connected to MQTT broker")
        else:
            logging.fatal("failed to connect to MQTT, code: %d\n", rc)

    def __on_message(self, client, userdata, msg):
        self.__msg_callback(msg.payload.decode())

    def __enter__(self):
        self.__client = Client(self.__client_id)
        self.__client.on_connect = self.__on_connect
        if self.__broker_username is not None:
            self.__client.username_pw_set(self.__broker_username, self.__broker_password)
        self.__client.connect(self.__address, self.__port)
        self.__client.loop_start()
        self.__client.subscribe(topic=topics.SEND_MESSAGE)
        self.__client.on_message = self.__on_message
        return self

    def __exit__(self, *args):
        self.__client.loop_stop()
        self.__client.disconnect()
