import argparse
import dataclasses as dc
import json
import logging
import re
import time
import traceback
from collections.abc import Callable
from queue import Queue
from threading import Thread
from typing import Any, TypeVar

import flask
import requests
from flask import Flask, Request

from whatsapp.error import (EmptyState, MissingParameters, UnknownEvent,
                            VerificationFailed)
from whatsapp.message import Incoming, MessageTypes, WhatsappChanges
from whatsapp.utils import middleware

logger = logging.getLogger(__name__)

STATE_TRIGGERS = TypeVar("STATE_TRIGGERS", str, tuple[MessageTypes, ...])

bot_options_parser = argparse.ArgumentParser()

bot_options_parser.add_argument(
    "-t", "--whatsapp-token", required=True, type=str, help="Whatsapp Meta API token"
)
bot_options_parser.add_argument(
    "--verify-token", type=str, help="The verify token. Used for set new callback URL"
)
# TODO add more options like endpoint, api_version etc

@dc.dataclass
class State:
    avaiable_states: list[tuple[Callable, STATE_TRIGGERS]] = dc.field(default_factory=list)
    "List of avaiable states"
    invalid_state: Callable = dc.field(default=None)
    "Triggered when don't trigger any state"

@dc.dataclass
class WhatsappBot:
    whatsapp_token: str = dc.field()
    "Whatsapp API token"
    verify_token: str = dc.field()
    "Verify token for set webhook url"
    endpoint: str = dc.field(default="https://graph.facebook.com")
    "META API endpoint"
    api_version: str = dc.field(default="v19.0")
    "Meta API version"
    flask_config: object = dc.field(default=None)
    "Flask config from object"
    flask_app: Flask = dc.field(default=None)
    "Flask app (created by create_app method)"
    _is_running: bool = dc.field(default=False)
    "True if bot is running"
    _server_queue: Queue = dc.field(default_factory=Queue)
    "Queue to store incoming messages"
    _state_handlers: dict[str, State] = dc.field(default_factory=dict)
    "Mapping to store state handlers"
    _user_states: dict[str, str] = dc.field(default_factory=dict)
    "Save user states by id"
    _initial_state: dict[str, State] = dc.field(default=None)
    "Initial state for a new user"
    _can_run_empty: bool = dc.field(default=False)

    def __post_init__(self):
        """
        Creates Flask app if not exists.
        """
        if self.flask_app is None:
            self.flask_app = self.create_app(self.flask_config)

        if self.verify_token is None:
            logger.warning("Verify token was not setted.")

    @property
    def bearer_token (self) -> str:
        """
        Returns the bearer token.
        """
        return f"Bearer {self.whatsapp_token}"

    def external_endpoint (self, bot_number_id: str) -> str:
        """
        Returns the external endpoint.

        Args:
            bot_number_id (str): The bot number ID.

        Returns:
            str: The external endpoint.
        """
        return f"{self.endpoint}/{self.api_version}/{bot_number_id}/messages"

    async def send_message (self, message: dict[str, Any], bot_number_id: str):
        """
        Sends a message.

        Args:
            message (dict): The message to send.
            bot_number_id (str): The bot number ID.
        """
        headers = { "Authorization": self.bearer_token, "Content-Type": "application/json" }
        payload = json.dumps(message)
        response = requests.post(
            self.external_endpoint(bot_number_id), data=payload, headers=headers
        )
        try:
            response.raise_for_status()
        
        except requests.exceptions.HTTPError as exc:
            logger.error(response.text)
            logger.error(f"Error sending message: {exc}")

    def handle_message (self, request: Request):
        """
        Handles incoming messages.

        Args:
            request (Request): The incoming request.

        Returns:
            str | dict: The response message.
        """
        if request.method == "GET":
            return self.webhook_verify_token(request)

        elif request.method == "POST":
            data = request.json
            if data.get("object") is None:
                raise UnknownEvent("Not a META API event.")

            for entry in data["entry"]:
                incomings = WhatsappChanges(**entry)
                for incoming in incomings.changes:
                    self.enqueue_update(incoming)

            return {"status": "ok"}

        logging.error(f"This method ({request}) is not allowed here, sorry cowboy.")

    def add_new_state (
        self, state: str, on_state_func: Callable,
        handler_trigger: str | MessageTypes | STATE_TRIGGERS
    ):
        """
        Adds a command to the state handler.

        Args:
            state (USER_STATE): The user state.
            handler (Callable): The command handler.
            command_or_pattern (str): The command or pattern.

        Raises:
            UnknownEvent: If the state is not valid.
        """
        if state not in self._state_handlers:
            self._state_handlers[state] = State()

        if self._initial_state is None:
            self._initial_state = state

        if isinstance(handler_trigger, MessageTypes):
            handler_trigger = ( handler_trigger, )

        if isinstance(handler_trigger, str):
            # If handler_trigger is a command, converts it to a regex pattern
            if handler_trigger.startswith("/"):
                handler_trigger = handler_trigger.lstrip("/")
                handler_trigger = rf"^/{handler_trigger}"

            # Just compiles the regex pattern
            else:
                handler_trigger = re.compile(handler_trigger)

        elif (
            isinstance(handler_trigger, tuple)
            and all(isinstance(item, MessageTypes) for item in handler_trigger)
        ):
            # Remove duplicates and (re-)converts to tuple
            handler_trigger = tuple(set(handler_trigger))

        else:
            raise UnknownEvent("Invalid handler trigger")

        self._state_handlers[state].avaiable_states.append((on_state_func, handler_trigger))

    def add_invalid_state (self, state: str, on_invalid_state_func: Callable):
        """
        Adds a command to the invalid state handler. If none wait for a valid state

        Args:
            state (USER_STATE): The user state.
            on_invalid_state_func (Callable): The command handler.

        Raises:
            UnknownEvent: If the state is not valid.
        """
        if state not in self._state_handlers:
            raise UnknownEvent(f"{state} is not a valid state")

        self._state_handlers[state].invalid_state = on_invalid_state_func

    def webhook_verify_token (self, request: Request) -> str:
        """
        Verifies the webhook token.

        Args:
            request (flask.request): The incoming request.

        Returns:
            str: The verification challenge.

        Raises:
            MissingParameters: If required parameters are missing.
            VerificationFailed: If the verification fails.
        """
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

    def create_app (self, config: object = None):
        """
        Creates the Flask application.

        Args:
            config: The Flask configuration.

        Returns:
            Flask: The Flask application.
        """
        app = Flask(__name__)
        app.config.from_object(config)

        @app.route("/", methods=["POST", "GET"])
        @middleware
        def webhook ():
            return self.handle_message(flask.request)

        @app.route("/healthcheck", methods=["GET"])
        def healthcheck ():
            return "Everything all right!"

        return app

    def start_webhook (
        self, host: str = "127.0.0.1", port: int = 8000, debug: bool = False,
        load_dot_env: bool = False, **server_options: dict[str, Any]
    ):
        """
        Starts the webhook server.

        Args:
            host (str): The server host.
            port (int): The server port.
            debug (bool): Indicates if debug mode is enabled.
            load_dot_env (bool): Indicates if .env file should be loaded.
            **server_options: Additional server options.
        """
        self._is_running = True
        server_app = Thread(
            name="flask_server",
            target=self.flask_app.run,
            daemon=True,
            args=(host, port, debug, load_dot_env),
            kwargs=server_options,
        )

        logger.info("Starting Server...")
        server_app.start()
        self._is_running = False

    async def run_forever (self, interval: float = 0.1):
        """
        Runs the bot forever.

        Args:
            interval (float): The interval between updates.
        """
        logger.info("Starting updater Event")
        if self._initial_state is None:
            raise EmptyState("No states are defined for the bot")

        while True:
            try:
                time.sleep(interval)
                incoming_update = self._server_queue.get()
                if incoming_update is None:
                    continue

                await self.process_update(incoming_update)

            except KeyboardInterrupt:
                break

            except Exception:
                logger.error(f"Unknown error: {traceback.format_exc()}")

    def enqueue_update (self, update: Incoming):
        """
        Enqueues an update.

        Args:
            update: The update to enqueue.
        """
        self._server_queue.put(update)

    async def process_update (self, incoming: Incoming):
        """
        Processes an update.

        Args:
            update: The update to process.
        """
        for message_idx in range(len(incoming.messages)):
            incoming._message_idx = message_idx

            # BUG Remove this
            import os
            json
            file_name = str(incoming.message.type) + ".json"
            if not os.path.exists(file_name):
                with open(file_name, "w") as f:
                    json.dump(json.loads(incoming.to_json()), f, indent=4)

            user_state_name = self._user_states.get(incoming.message.from_, self._initial_state)

            if user_state_name not in self._state_handlers:
                raise UnknownEvent(
                    f"{user_state_name} is not a valid state.\n"
                    f"Valid states: {list(self._state_handlers)}"
                )
            current_state = self._state_handlers[user_state_name]

            new_state = None
            for handler, pattern_to_match in current_state.avaiable_states:
                if (
                    (
                        isinstance(pattern_to_match, tuple)
                        and incoming.message.type in pattern_to_match
                    )
                    or (
                        isinstance(pattern_to_match, str)
                        and re.match(pattern_to_match, incoming.message.message_value)
                    )
                ):
                    new_state = await handler(self, incoming)

                    break

            else:
                if current_state.invalid_state is not None:
                    new_state = await current_state.invalid_state(self, incoming)

                logger.warning(
                    f"'{incoming.message.message_value}' Not matched with any command"
                )

            if new_state is not None:
                self._user_states[incoming.message.from_] = new_state
