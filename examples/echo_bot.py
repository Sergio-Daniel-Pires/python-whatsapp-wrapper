import asyncio
import logging

from whatsapp.bot import WhatsappBot, bot_options_parser
from whatsapp.message import Incoming, MessageTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

START = range(1)

async def echo (bot: WhatsappBot, incoming: Incoming) -> int:
    """
    Echoes the message received from the user.

    Args:
        bot (WhatsappBot): The WhatsappBot instance.
        update (TextMessage): The message received from the user.
        incoming (Incoming): The incoming message object.

    Returns:
        int: The value representing the next state of the bot.
    """
    echo_msg = incoming.message.to_reply(incoming.message.from_, incoming.message.message_value)
    await bot.send_message(echo_msg, incoming.metadata.phone_number_id)

    return START

async def main (args: list[str] = None):
    args = bot_options_parser.parse_args(args)

    bot = WhatsappBot(
        verify_token=args.verify_token, whatsapp_token=args.whatsapp_token
    )

    bot.add_new_state(START, echo, MessageTypes.TEXT)

    bot.start_webhook()

    await bot.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
