.. _production_deployment:

Deploying Bots in Production
============================

Now that your bot (or bots) are finished, it's time to deploy them to production. Whether you have a single bot or multiple bots, this section will guide you on how to deploy a bot in production using two separate services: A ``server`` to handle all requests and each ``bot`` individually.

WSGI Server
-----------

When deploying a bot in production, you'll need a WSGI server to manage multiple requests simultaneously. Popular options include Gunicorn, Uvicorn, and many others. If you're deploying only one bot, you can simply start the server and bot together using a command like this:

.. code-block:: bash

    gunicorn --workers=2 my_bot:app

Full Example with Multiple Bots
-------------------------------

If you have more than one bot, you might want to create isolated contexts for each bot application and use multiple WSGI workers to dispatch all requests to the correct bots. In this example, we'll use ``Redis`` as a message queue, but you can use any queue system that suits your needs.

Here's how you can structure your deployment:

.. code-block:: python
    :caption: Utility file with customized WhatsappBot class

    class CustomWhatsappBot(WhatsappBot):
        redis_conn = Redis()

        def enqueue_update(self, update):
            # Bot numbers are not always the same
            # So they need to be extracted from the incoming update

            bot_number = update.metadata.display_phone_number

            self.redis_conn.lpush(f"whatsapp:updates:{bot_number}", update.to_json())

        def get_update(self):
            # Bot number is consistent here, as we're retrieving updates for the bot

            return self.redis_conn.lpop(f"whatsapp:updates:{self.bot_number}")

.. code-block:: python
    :caption: wsgi_app.py

    message_gateway = CustomWhatsappBot(WHATSAPP_TOKEN, VERIFY_TOKEN, _can_run_empty=True)

    # Create Flask app (Gunicorn will use this)
    app = message_gateway.create_app()

    if __name__ == "__main__":
        app.run()

.. code-block:: python
    :caption: custom_bot.py

    async def main():
        bot = CustomWhatsappBot(WHATSAPP_TOKEN, VERIFY_TOKEN, BOT_NUMBER)

        """
        Logic to handle incoming messages is omitted here
        """

        await bot.run_forever()

    if __name__ == "__main__":
        asyncio.run(main())

Start everything together and voilà! You have a production-ready bot!

.. note::
    There are many ways to deploy a bot in production—this is just one of them. You can use any other queue system, even a database to store updates, or opt for a robust queue system like RabbitMQ or Kafka. The possibilities are vast; if you have a better way to deploy your bot, feel free to do it and share your approach with us!


.. toctree::
    :hidden:

