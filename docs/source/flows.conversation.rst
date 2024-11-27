Starting with Flows
===================

WhatsApp flows perform three main tasks:
 * Inform the server about the screen where the user exited the flow.
 * Define the next screen that the user will see.
 * Handle data exchange between the server and user.

.. note::
    If you need to track flows user by user, you can define a ``flow_token`` when starting flow.

Starting a Flow
---------------

For flows that don't require input data to start, such as a login page, Meta will initiate the flow on WhatsApp at the first screen without requesting data from the server.

Ongoing Flow
------------

When the user clicks the ``continue`` button on a screen, Meta sends the interaction content to the server and waits for the next screen to be displayed. This content is encrypted using the public key you uploaded earlier. To process it, you must decrypt the content using the private key you saved, with the method :py:meth:`whatsapp.crypto.decrypt_request`. The decrypted content will be a JSON with the following structure:

.. code-block:: json
    {
        "data": {}, // Optional data
        "flow_token": "set_flow_token", // If flow_token was set during send
        "screen": "CURRENT_SCREEN",
        "action": "data_exchange", // Indicates server will send data for the next screen
        "version": "3.0" // Flow API version
    }

The server will wait up to 10 seconds for data or the name of the next screen. If nothing is received, WhatsApp will display a timeout message. The expected response should look like this:

.. code-block:: json
    {
        "screen": "NEXT_SCREEN",
        "data": { "variable_name": "value" }
    }

Handling Files in a Flow
~~~~~~~~~~~~~~~~~~~~~~~~

The server response may include files uploaded by the user. In such cases, you will receive a message like the following:

.. code-block:: json
    [{
        "file_name": "file_named.jpg",
        "media_id": "218fd366-324d-4b41-8be9-c28c46768d0b",
        "cdn_url": "https://mmg.whatsapp.net/v/t62.66612-24/...15_n.enc?ccb=11-4&oh=01_..._nc_sid=5e03e0&mms3=true",
        "encryption_metadata": {
            "encryption_key": "eZVCf...o4SfhsTBzxA8NPWMg=",
            "hmac_key": "Ovq1pXbLCR4...+KouvgctptsxyYZps=",
            "iv": "fpqP9mTFoAD5JYMOJa5glQ==",
            "plaintext_hash": "aQaNI...bjzxHfu9aeyN4PhpA=",
            "encrypted_hash": "+TsAg...aAm1HxJT9O7zdVgV8="
        }
    }]

You can download the file using the provided CDN URL and decrypt it using the method :py:meth:`whatsapp.crypto.decrypt_media_content`.

Finishing a Flow
----------------

At the end of a flow, the server will send a message to the default callback server containing an interactive message, such as:

.. code-block:: json
    {
        ...
        {
            "type": "interactive",
            "interactive": {
                "type": "nfm_reply",
                "nfm_reply": {
                    "response_json": "{\"flow_token\":\"set_flow_token\"}",
                    "body": "Sent",
                    "name": "flow"
                }
            }
        }
        ...
    }

You can use the flow response JSON to store any required data.
