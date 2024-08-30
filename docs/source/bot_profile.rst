Bot Profile
===========

When setting up a bot, you can configure its profile to provide essential information to users. The bot profile includes details such as the bot's name, description, and profile picture.

.. _bot_profile_components:

Components
----------

All components of the bot profile can be configured via the Meta Developer website, but it's often easier and more efficient to manage them using the API: :py:class:`whatsapp.config_account.ProfileComponents`.

.. note::
    Components cannot be set individually; you must set all of them at once. If you want to incrementally update the profile, you must first retrieve the current profile using :py:meth:`whatsapp.config_account.ProfileComponents.load_profile`, update the desired fields, and then overwrite the entire profile using :py:meth:`whatsapp.config_account.ProfileComponents.set_current_config`.

Commands
~~~~~~~~

Commands are displayed to users when they type `/` in the chat, such as ``/help``. These commands allow users to quickly access bot features and perform specific actions.

Prompts
~~~~~~~

Prompts are predefined messages that users can send to interact with the bot. They facilitate quick communication and guide users through common tasks.

Welcome Message
~~~~~~~~~~~~~~~

You can enable or disable the bot's welcome message, which is shown only the first time a user starts a chat with the bot. This message provides an opportunity to introduce the bot and highlight its capabilities.

Profile Data
------------

Picture
~~~~~~~

To be updated.
