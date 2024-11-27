Before Starting with Flows
==========================

Configure the Public Key
------------------------

Before creating a flow, you need to submit a public key to Meta. This key is used to encrypt user data, such as messages, steps, and media. To submit the public key, follow these steps:

Steps:
  1. Generate a new RSA 2048 3DES key using :py:meth:`whatsapp.crypto.generate_rsa_private_key`. Save the private key in a secure location, as it will be required to decrypt data.
  2. Extract the public key from the private key using :py:meth:`whatsapp.crypto.extract_public_key_from_private`.
  3. Upload the public key to Meta using :py:meth:`whatsapp.file_handler.send_whatsapp_business_encryption`, specifying the bot's number ID.

Configure the Flow Endpoint
---------------------------

Flows do not use the same endpoint as the Meta API. Each flow can have a different endpoint, but once the URL is set, it is **FIXED FOREVER**. Configure a new endpoint in your message handler or use a separate server to handle the flow.

Flow Endpoint Health Verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When setting a new endpoint, Meta will send a ``POST`` request to the endpoint with the following content:

.. code-block:: json

    {
        "encrypted_flow_data": "hXGXjcC...oRfyZY52eBHN2HAxbQ==",
        "encrypted_aes_key": "ojM2Vu+Hg...SqoGUHKYbfEa3AZwNA==",
        "initial_vector": "u2R1PtoAn+wC1do9A5fyDA=="
    }

This content is encrypted with the public key you previously uploaded. To process it, you must decrypt it using the private key you saved, via :py:meth:`whatsapp.crypto.decrypt_request`. The decrypted content will be a JSON with the following structure:

.. code-block:: json

    {
        "version": "3.0",
        "action": "ping"
    }

You must respond with the following JSON:

.. code-block:: json

    {
        "data": {
            "status": "active"
        }
    }

Before sending the response, you must encrypt it with the public key you uploaded earlier, using :py:meth:`whatsapp.crypto.encrypt_response`.

Now you are ready to create a flow!
