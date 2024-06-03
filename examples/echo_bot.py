import asyncio
import logging

from whatsapp.bot import WhatsappBot
from whatsapp.message import TextMessage
from whatsapp.models import Incoming

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

START = range(1)

async def echo (bot: WhatsappBot, update: TextMessage, incoming: Incoming):
    if not isinstance(update, TextMessage):
        return None

    echo_txt = update.message_value.split("/echo")[1].strip()[::-1]
    echo_msg = update.to_reply(update.from_, echo_txt)
    await bot.send_message(echo_msg, incoming.metadata.phone_number_id)

    return START

async def main():
    bot = WhatsappBot(verify_token="VERIFY_TOKEN", whatsapp_token="EAAP4fM5pvHEBOZCqmcyJVZCU8qMKriBUZCTdEPlS7C3uqNNczubAKavea9zDnUxDIsnJVGmGeiFi99apBRVHZBRFwRhSp46ZBRfidzlOKj8K8wa62pZBYQYJlZCEv1Yix89ZAe7eMpHdc1iFolZCzxMlto5LIBrw58mZBq4KpIG6ZBiVTdZAipa63BdWZAZBXCLstmCK9F")

    bot.add_command(START, echo, "/echo")

    bot.start_webhook()

    await bot.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
