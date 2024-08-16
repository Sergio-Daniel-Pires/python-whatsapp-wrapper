🤖 Want a whatsapp bot? You're in the right place.
==================================================

📖 Introduction
---------------

A high-level Python wrapper for the WhatsApp API, providing easy abstraction.

A huge thanks to `Pyton-Telegram-Bot`_ team for their impressive work on Telegram bots, which inspired me to create this wrapper.

📱 Whatsapp API Supports
------------------------

Tested in version ``v19.0``, but you can try older versions by changing ``api_version`` in `whatsapp.bot.WhatsappBot.api_version`.

🛠️ Before start
---------------

Before you can create your own bots, you need to follow some steps to become a `Meta API Developer`_.

**YOU NEED**  to become a Meta developer to use their API. You can find the step-by-step guide here: `Facebook Developers WhatsApp API`_

.. warning::
    It's preferable to have an extra/new SIM card to register your business account (don't try with your personal SIM, this action will **ERASE** all your whatsapp data), but they give you some free credits to get started.

🚀 Installation
---------------

We're on PyPI! So you can easy install using:

.. code-block:: bash

    pip install python-whatsapp-wrapper

Or directly by cloning project's GitHub repository:

.. code-block:: bash

    git clone https://github.com/Sergio-Daniel-Pires/python-whatsapp-wrapper
    cd python-whatsapp-wrapper
    pip install .

🤔 How I made my own bot?
-------------------------

Our repository contains many examples that you can just click-and-run.
You might want to try ``echo_bot.py``, a bot that returns any text you send it.

📄 License
----------

MIT

.. _Meta API Developer: https://developers.facebook.com/products/whatsapp/
.. _Pyton-Telegram-Bot: https://github.com/python-telegram-bot/python-telegram-bot
.. _Facebook Developers WhatsApp API: https://developers.facebook.com/docs/whatsapp/getting-started