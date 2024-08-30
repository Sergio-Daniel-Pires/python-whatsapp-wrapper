import asyncio
import logging

from whatsapp.bot import WhatsappBot, bot_options_parser
from whatsapp.messages import Incoming, MessageTypes, TextMessage
from whatsapp.utils import read_message

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

START = range(1)

@read_message
async def echo (bot: WhatsappBot, incoming: Incoming) -> int:
    """
    Echo function to send the same message back to the user.

    :param bot: WhatsappBot instance.
    :param incoming: Incoming message object.
    :return: Next bot state
    """
    echo_msg = None

    match incoming.message.type:
        case MessageTypes.TEXT:
            echo_msg = TextMessage.to_send(incoming.message.from_, incoming.message.message_value)

    try:
        await bot.send_message(echo_msg, incoming.metadata.phone_number_id)

    except Exception as exc:
        logger.error(f"Error sending message: {exc}")

    # Returns to initial state
    return START

async def main (args: list[str] = None):
    # Parse args from terminal, like "python echo_bot.py --phone_number_id=1234567890"
    user_args = bot_options_parser.parse_args(args)
    user_args_as_kwargs = dict(user_args._get_kwargs())

    bot: WhatsappBot = WhatsappBot.from_dict(user_args_as_kwargs)

    # Add a new state to the bot, that captures all text messages
    bot.add_new_state(START, echo, MessageTypes.TEXT)

    # Start webhook server in a separeted Thread
    bot.start_webhook()

    # Verify updates in shared queue
    await bot.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
