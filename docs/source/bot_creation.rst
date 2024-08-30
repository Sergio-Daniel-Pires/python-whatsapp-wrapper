Create Your Own Bot
===================

To create a functional bot, you need:

    * States to manage the conversation flow.
    * Functions associated with each state that perform actions based on user input.
    * Return next state key state function.

Registering a New State
-----------------------

To register a new state, you first need to create an ``async function`` that accepts two parameters: :py:class:`whatsapp.bot.WhatsappBot` and :py:class:`whatsapp.messages.Incoming`.

.. note::
    You can define any hashable object as a state, but my personal preference is to use strings or integers.

The :py:class:`whatsapp.messages.Incoming` class has many attributes, but for now, let's focus on the ``message`` property, which contains the user's message.

Here is the basic structure of a state function:

.. code-block:: python

    async def my_state(bot: WhatsappBot, incoming: Incoming) -> str | int:
        """My state function"""

To register a new state, use the :py:meth:`whatsapp.bot.WhatsappBot.add_new_state` method. This method links the current state to the previous state, specifies what type of message or structure triggers this state, and defines the next state that the bot should wait for after processing. Let's create an example that echoes the user's message:

.. code-block:: python

    START = range(1)

    async def echo_msg(bot: WhatsappBot, incoming: Incoming) -> str | int:
        msg_obj = TextMessage.to_send(incoming.message.from_, incoming.message.message_value)
        
        await bot.send_message(echo_msg, incoming.metadata.phone_number_id)

        return START

    bot = WhatsappBot(WHATSAPP_TOKEN, VERIFY_TOKEN)
    bot.add_new_state(START, echo_msg, TextMessage)

And that's it! You have successfully registered a bot state that echoes user messages whenever it receives a :py:attr:`whatsapp.messages.MessageTypes.TEXT` message. But we're not done yet—you can enhance this bot further by using additional methods from the ``whatsapp`` module and following some best practices.

Automatic Message Reading
~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to read user messages without having to recreate a :py:class:`whatsapp.messages.ReadMessage` object in every state function, you can use the :py:meth:`whatsapp.utils.read_message` decorator. This decorator will automatically read the message each time the state function is called.

Handling Different Types of Messages
------------------------------------

Your bot can handle different types of messages using two methods:

Message Type as a Trigger
~~~~~~~~~~~~~~~~~~~~~~~~~

You can trigger a state based on a single message type or a tuple of types. For example, you could trigger on ``(MessageTypes.IMAGE, MessageTypes.VIDEO)``.

Regex Match as a Trigger
~~~~~~~~~~~~~~~~~~~~~~~~

You can define a regex pattern to match the user's message. For example, ``r'^[0-9]$'`` for numeric input or ``r'^/start$'`` for commands. If you use command-like patterns, it's recommended to register the command in the bot profile using the :py:meth:`whatsapp.config_account.ProfileComponents.add_command` method. See more at :ref:`bot_profile_components`.

Handling Invalid States
~~~~~~~~~~~~~~~~~~~~~~~

If no state is triggered, you can add an invalid state handler using :py:meth:`whatsapp.bot.WhatsappBot.add_invalid_state`. This handler can be used to reset the user's state, provide help, or simply do nothing.
