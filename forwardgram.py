import os
from telethon import TelegramClient, events
from telethon.tl.types import InputChannel
import yaml
import sys
import logging
from dotenv import load_dotenv, find_dotenv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)


def start(config):
    try:
        api_id = os.environ.get('APP_ID')
        api_hash = os.environ.get('API_HASH')
        client = TelegramClient(config["session_name"], api_id, api_hash)
        client.start()

        # dialogs = client.get_dialogs()
        # print(dialogs)

        input_channels_entities = []
        output_channel_entities = []
        for d in client.iter_dialogs():
            if d.name in config["input_channel_names"] or d.entity.id in config["input_channel_ids"]:
                logging.info(f"input channel name: {d.name}, id: {d.id}")
                input_channels_entities.append(
                    InputChannel(d.entity.id, d.entity.access_hash))
            if d.name in config["output_channel_names"] or d.entity.id in config["output_channel_ids"]:
                logging.info(f"output channel name: {d.name}, id: {d.id}")
                output_channel_entities.append(
                    InputChannel(d.entity.id, d.entity.access_hash))

        if not output_channel_entities:
            logger.error(
                f"Could not find any output channels in the user's dialogs")
            sys.exit(1)

        if not input_channels_entities:
            logger.error(
                f"Could not find any input channels in the user's dialogs")
            sys.exit(1)

        logging.info(
            f"Listening on {len(input_channels_entities)} channels. Forwarding messages to {len(output_channel_entities)} channels.")

        @client.on(events.NewMessage(chats=input_channels_entities))
        async def handler(event):
            for output_channel in output_channel_entities:
                if not event.message.media:
                    try:
                        modify_event_message(event.message)
                        logging.info(
                            f"send message {event.message} to channel id: {output_channel.channel_id}")
                        await client.send_message(output_channel, event.message)
                    except Exception as error:
                        logging.error(f"Error: {error}")

        client.run_until_disconnected()
    except ConnectionError:  # catches the ConnectionError and starts the connections process again
        print('ConnectionError... Reconnection now...')
        start()
    except Exception as error:
        print('General error was occured, Reconnection now...', error)
        start()


def modify_event_message(event_message):
    text_message = str(event_message.message)
    text_message = text_message.replace(
        '\n--------------------\n\n-\nלא המלצה', '')
    event_message.message = text_message


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    with open('./config.yml', 'rb') as f:
        config = yaml.safe_load(f)
    start(config)
