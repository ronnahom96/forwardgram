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
    api_id = os.environ.get('APP_ID')
    api_hash = os.environ.get('API_HASH')
    client = TelegramClient(config["session_name"], api_id, api_hash)
    client.start()

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
            if event.message.media:
                print('media message')
            else:
                logging.info(
                    f"send message {vars(event.message).get('message', '')} to channel id: {output_channel.channel_id}")
                await client.send_message(output_channel, event.message)

    client.run_until_disconnected()


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    with open('./config.yml', 'rb') as f:
        config = yaml.safe_load(f)
    start(config)
