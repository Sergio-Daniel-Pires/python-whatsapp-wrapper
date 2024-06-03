import dataclasses as dc
import json
import logging
import re
import time
import traceback
from collections.abc import Callable
from queue import Queue
from threading import Thread
from typing import Any

import flask
import requests
from flask import Flask
from requests import Request

from whatsapp.error import (EmptyState, MissingParameters, UnknownEvent,
                            VerificationFailed)
from whatsapp.models import USER_STATE, Incoming, IncomingPayload
from whatsapp.utils import middleware

logger = logging.getLogger(__name__)

TEXT_COMMAND = r".*"

@dc.dataclass
class WhatsappBot:
    # Local config
    whatsapp_token: str = dc.field()
    verify_token: str = dc.field()

    # Meta API config
    endpoint: str = dc.field(default="https://graph.facebook.com")
    api_version: str = dc.field(default="v19.0")

    # Server
    flask_config: Any = dc.field(default=None)
    flask_app: Flask = dc.field(default=None)
    is_running: bool = dc.field(default=False)

    # Internal vars
    _server_queue: Queue = dc.field(default_factory=Queue)
    _state_handlers: dict[USER_STATE, list[tuple[str, Callable]]] = dc.field(default_factory=dict)
    _user_states: dict[str, USER_STATE] = dc.field(default_factory=dict)
    _initial_state: USER_STATE = dc.field(default=None)

    def __post_init__ (self):
        if self.flask_app is None:
            self.flask_app = self.create_app(self.flask_config)

    @property
    def bearer_token (self):
        return f"Bearer {self.whatsapp_token}"

    def external_endpoint (self, bot_number_id: str):
        return f"{self.endpoint}/{self.api_version}/{bot_number_id}/messages"

    async def send_message (self, message: dict[str, Any], bot_number_id: str):
        headers = { "Authorization": self.bearer_token, "Content-Type": "application/json" }

        payload = json.dumps(message)

        response = requests.post(
            self.external_endpoint(bot_number_id), data=payload, headers=headers
        )

        response.raise_for_status()

    def handle_message (self, request: Request) -> str | dict[str, Any]:
        if request.method == "GET":
            return self.webhook_verify_token(request)

        elif request.method == "POST":
            data = request.json

            if data.get("object") is None:
                raise UnknownEvent("Not an META API event.")

            # Handle user updates
            for entry in data["entry"]:
                incomings = IncomingPayload(**entry)

                for incoming in incomings.changes:
                    self.enqueue_update(incoming)

            return { "status": "ok" }

        logging.error(f"This method ({request}) is not allowed here, sorry cowboy.")

    def add_command (
        self, state: USER_STATE, handler: Callable, command_or_pattern: str = TEXT_COMMAND
    ):
        """
        Add command to state handler
        """
        # Set users initial states
        if state not in self._state_handlers:
            self._state_handlers[state] = []

        if self._initial_state is None:
            self._initial_state = state

        if command_or_pattern == TEXT_COMMAND:
            logger.warning("WARNING: Regex to accepts all are setted")

        # Set new command
        if command_or_pattern.startswith("/"):
            command_or_pattern = command_or_pattern.lstrip("/")
            command_or_pattern = rf"^/{command_or_pattern}"

        self._state_handlers[state].append(( command_or_pattern, handler ))

    def webhook_verify_token (self, request: flask.request) -> str:
        try:
            mode = request.args["hub.mode"]
            token = request.args["hub.verify_token"]
            challenge = request.args["hub.challenge"]

        except KeyError as exc:
            raise MissingParameters(f"{exc.args} are required parameters")

        except Exception as exc:
            logging.error(f"Unknown error: {exc}")

        if mode != "subscribe" or token != self.verify_token:
            raise VerificationFailed("Invalid mode or different verify token")

        return challenge

    def create_app (self, config = None):
        """
        Creates flask app
        """
        app = Flask(__name__)

        app.config.from_object(config)

        @app.route("/", methods=[ "POST", "GET" ])
        @middleware
        def webhook ():
            return self.handle_message(flask.request)

        @app.route("/healthcheck", methods=[ "GET" ])
        def healthcheck ():
            return "Everthing all right!"

        return app

    def start_webhook (
        self, host: str = "127.0.0.1", port: int = 8000, debug: bool = False,
        load_dot_env: bool = False, **server_options: Any
    ):
        self.is_running = True
        server_app = Thread(
            name="flask_server", target=self.flask_app.run, daemon=True,
            args=(host, port, debug, load_dot_env), kwargs=server_options
        )

        logger.info("Starting Server...")
        server_app.start()
        self.is_running = False

    async def run_forever (self, interval: float = 0.1):
        logger.info("Starting updater Event")

        if self._initial_state is None:
            raise EmptyState("No states are defined to bot")

        while True:
            try:
                time.sleep(interval)
                incoming_update = self._server_queue.get()
                if incoming_update is None:
                    continue

                await self.process_update(incoming_update)

            except KeyboardInterrupt:
                break

            except Exception as exc:
                logger.error(f"Unk error: {traceback.format_exc()}")

    def enqueue_update (self, update: Any):
        self._server_queue.put(update)

    async def process_update (self, update: Any):
        if isinstance(update, Incoming):
            for message in update.messages:
                user_state_name = self._user_states.get(message.from_, self._initial_state)
                if user_state_name not in self._state_handlers:
                    raise UnknownEvent(
                        f"{user_state_name} is not a valid state.\n"
                        f"Valid states: {list(self._state_handlers)}"
                    )

                avaiable_states = self._state_handlers[user_state_name]

                for pattern_to_match, handler in avaiable_states:
                    if re.match(pattern_to_match, message.message_value):
                        new_state = await handler(self, message, update)

                        if new_state is not None:
                            self._user_states[message.from_] = new_state

                else:
                    # TODO
                    ...

        # Send message
        else:
            # TODO
            ...
