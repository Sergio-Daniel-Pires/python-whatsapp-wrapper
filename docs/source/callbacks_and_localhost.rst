Meta API Callback
=================

Introduction
------------

To use the Meta API, you need to create a callback server to receive updates from WhatsApp. This server must have a secure HTTPS endpoint that can accept both POST and GET requests.

Register callback endpoint
--------------------------

Steps:
    1. Go to your apps in `Facebook Developers Apps`_ and select respective app.
    2. Left menu, click on ``Whatsapp`` -> ``Config``.
    3. Under the ``Webhook`` section, set your callback URL and your ``verification token``.

Verification token
~~~~~~~~~~~~~~~~~~

The ``verification token`` are a secret key that Meta will GET from the webhook URL and use as a challenge. So configure the same token used in :py:attr:`whatsapp.bot.WhatsappBot.verify_token`.

Localhost testing
-----------------

For testing your webhook in a local development environment, you'll need a tool to create a reverse proxy to your localhost. My personal favorite is `Ngrok`_, as it is easy to use and widely supported.

.. warning::
    However, be aware that Meta might occasionally block ``Ngrok``. In such cases, you can use alternative tools like `Serveo`_.

Alternatively, you can implement a publish-subscribe architecture by using an online server with a public IP. This server can register callback data into a shared database like Redis, allowing you to consume the data directly from your localhost. For more details on this method, refer to :ref:`production_deployment`.

.. _Facebook Developers Apps: https://developers.facebook.com/apps
.. _Ngrok: https://ngrok.com/
.. _Serveo: https://serveo.net/
