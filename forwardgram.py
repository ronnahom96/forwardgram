import os
from telethon import TelegramClient, events
from telethon.tl.types import InputChannel
import yaml
import sys
import logging
from dotenv import load_dotenv, find_dotenv

MAX_RETRIES_NUMBER = 3
MAX_IGNORE_MESSAGE_COUNTER = 7
VIP_KEYWORD = 'Premium'
CRYPTO_NOTIFICATION_SIGN = '⚡️⚡️'
# VIP_ID = 1792179423

class Forwardgram:
    def __init__(self, client, config, logger):
        self.client = client
        self.config = config
        self.logger = logger
        self.input_channels_entities = []
        self.output_channel_entities = []
        self.channel_ids_names = {}
        self.retries_number = 0
        self.ignore_message_counter = 0

    def start(self):
        if (self.retries_number > MAX_RETRIES_NUMBER):
            return self.logger.info(f"We have reached to the maximum retries number")

        try:
            self.client.start()

            self.input_channels_entities, self.output_channel_entities, self.channel_ids_names = self.build_input_output_channels(
                self.config)

            self.logger.info(
                f"Listening on {len(self.input_channels_entities)} channels. Forwarding messages to {len(self.output_channel_entities)} channels.")

            @self.client.on(events.NewMessage(chats=self.input_channels_entities))
            async def handler(event):
                for output_channel in self.output_channel_entities:
                    if event.message.media:
                        return

                    try:
                        text_message = self.extract_text_from_event(event)
                        channel_name = self.channel_ids_names[output_channel.channel_id]
                        if VIP_KEYWORD in channel_name:
                            self.logger.info(
                                f"send premium group message {text_message} group id: {output_channel.channel_id}")
                            await self.client.send_message(output_channel, event.message)
                        elif CRYPTO_NOTIFICATION_SIGN in text_message:
                            if self.ignore_message_counter % MAX_IGNORE_MESSAGE_COUNTER == 0:
                                self.modify_event_message(event.message)
                                self.logger.info(f"send regular group message {vars(event.message).get('message', 'No message')} to channel id: {output_channel.channel_id}")
                                await self.client.send_message(output_channel, event.message)

                            self.logger.info(f"Increase the ignore message counter from {self.ignore_message_counter} to {self.ignore_message_counter + 1}")
                            self.ignore_message_counter = self.ignore_message_counter + 1                            
                        else:
                            self.logger.info(f"skip on the message {text_message} because it is not a crypto notification and it not a premium channel")
                    except Exception as error:
                        self.logger.error(f"Error: {error}")

            self.client.run_until_disconnected()
        except ConnectionError:  # catches the ConnectionError and starts the connections process again
            self.logger.info('ConnectionError... Reconnection now...')
            self.start()
        except Exception as error:
            self.logger.error(
                f"General error was occurred, Reconnection now... {error}")
            self.retries_number = self.retries_number + 1
            self.start()

    def build_input_output_channels(self, config):
        input_channels_entities = []
        output_channel_entities = []
        channel_ids_names = {}
        for d in self.client.iter_dialogs():
            if d.name in config["input_channel_names"] or d.entity.id in config["input_channel_ids"]:
                self.logger.info(f"input channel name: {d.name}, id: {d.id}")
                input_channels_entities.append(
                    InputChannel(d.entity.id, d.entity.access_hash))
                channel_ids_names[d.entity.id] = d.name
            if d.name in config["output_channel_names"] or d.entity.id in config["output_channel_ids"]:
                self.logger.info(f"output channel name: {d.name}, id: {d.id}")
                output_channel_entities.append(
                    InputChannel(d.entity.id, d.entity.access_hash))
                channel_ids_names[d.entity.id] = d.name

        if not output_channel_entities:
            self.logger.error(
                f"Could not find any output channels in the user's dialogs")
            sys.exit(1)

        if not input_channels_entities:
            self.logger.error(
                f"Could not find any input channels in the user's dialogs")
            sys.exit(1)

        return input_channels_entities, output_channel_entities, channel_ids_names

    @staticmethod
    def extract_text_from_event(event):
        return vars(event.message).get('message', 'No message')

    @staticmethod
    def modify_event_message(event_message):
        text_message = str(event_message.message)
        text_message = text_message.replace(
            '\n--------------------\n\n-\nלא המלצה', '')
        event_message.message = text_message


def build_logger():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger('telethon').setLevel(level=logging.WARNING)
    return logging.getLogger(__name__)


def init_telegram_client(config):
    api_id = os.environ.get('APP_ID')
    api_hash = os.environ.get('API_HASH')
    return TelegramClient(config["session_name"], api_id, api_hash)


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    logger = build_logger()

    with open('./config.yml', 'rb') as f:
        config = yaml.safe_load(f)
        telegram_client = init_telegram_client(config)
        forwardgram = Forwardgram(telegram_client, config, logger)
        forwardgram.start()
