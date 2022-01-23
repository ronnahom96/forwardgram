from telethon import TelegramClient, events, sync
from telethon.tl.types import InputChannel
import yaml
import sys
import logging
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)


def start(config):
    print('config["session_name"]', config["session_name"])
    client = TelegramClient(config["session_name"],
                            config["api_id"],
                            config["api_hash"])
    client.start()

    # dialogs = client.get_dialogs()
    # print(dialogs)

    input_channels_entities = []
    output_channel_entities = []
    for d in client.iter_dialogs():
        if d.name in config["input_channel_names"] or d.entity.id in config["input_channel_ids"]:
            input_channels_entities.append(
                InputChannel(d.entity.id, d.entity.access_hash))
        if d.name in config["output_channel_names"] or d.entity.id in config["output_channel_ids"]:
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
            await client.send_message(output_channel, event.message)

    client.run_until_disconnected()


if __name__ == "__main__":
    # with open('./config.yml', 'rb') as f:
    #     config = yaml.safe_load(f)
    config = os.environ
    start(config)
