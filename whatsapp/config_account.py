import dataclasses as dc
from typing import Any, Self

import requests
from dataclasses_json import dataclass_json

from whatsapp.bot import WhatsappBot


@dataclass_json
@dc.dataclass
class ProfileCommand:
    command_name: str = dc.field()
    "Command name. Max 32 characters"
    command_description: str = dc.field()
    "Command description. Max 256 characters, emojis are not supported"

@dataclass_json
@dc.dataclass
class ProfileComponents:
    welcome_message: bool = dc.field(default=False)
    "Enable/disable welcome message"
    commands: list[ProfileCommand] = dc.field(default_factory=list)
    "Commands like '/comamnd'. Max 32 commands"
    prompts: list[str] = dc.field(default_factory=list)

    @classmethod
    def get_current_config (cls, bot: WhatsappBot, bot_number_id: str) -> dict[str, Any]:
        headers = { "Authorization": bot.bearer_token }
        # TODO: Fix this bad replace
        endpoint = bot.external_endpoint(bot_number_id, "fields=conversational_automation")
        endpoint = endpoint.replace("/fields", "?fields")

        return requests.get(endpoint, headers=headers).json()

    @classmethod
    def load_profile(cls, bot: WhatsappBot, bot_number_id: str) -> Self:
        print(cls.get_current_config(bot, bot_number_id))
        return cls.from_dict(cls.get_current_config(bot, bot_number_id))

    def set_current_config (self, bot: WhatsappBot, bot_number_id: str):
        headers = { "Authorization": bot.bearer_token, "Content-Type": "application/json" }
        endpoint = bot.external_endpoint(bot_number_id, "conversational_automation")
        data = self.to_json()

        return requests.post(endpoint, headers=headers, data=data).json()

    def add_command (self, command_name: str, command_description):
        """
        Add a command to a given Profile

        :param command_name: Command name that will appear when user tap profile or keyboard
        :param command_description: Command description for help user
        """
        command_name = command_name.lstrip("/")
        self.commands.append(ProfileCommand(command_name, command_description))
