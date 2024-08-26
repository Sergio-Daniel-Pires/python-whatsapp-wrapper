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
from dataclasses_json import dataclass_json
from flask import Flask, Request

from whatsapp.error import (EmptyState, MissingParameters, UnknownEvent,
                            VerificationFailed)
from whatsapp.messages import (USER_STATE, Incoming, MessageTypes,
                               WhatsappChanges)
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
bot_options_parser.add_argument(
    "--port", type=int, help="App port"
)
# TODO add more options like endpoint, api_version etc

@dc.dataclass
class State:
    """
    State class to store handler triggers
    """
    avaiable_states: list[tuple[Callable, STATE_TRIGGERS]] = dc.field(default_factory=list)
    "List of avaiable states"
    invalid_state: Callable = dc.field(default=None)
    "Triggered when don't trigger any state"

@dataclass_json
@dc.dataclass
class WhatsappBot:
    """
    Whatsapp Bot class
    """
    whatsapp_token: str = dc.field()
    "Whatsapp API token"
    verify_token: str = dc.field()
    "Verify token for set webhook url"
    endpoint: str = dc.field(default="https://graph.facebook.com")
    "META API endpoint"
    api_version: str = dc.field(default="v19.0")
    "Meta API version"
    welcome_message: str = dc.field(default="Hello, I'm using python-whatsapp-wrapper!")
    "Welcome message to send when user start a conversation"
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
        Returns the bearer token
        """
        return f"Bearer {self.whatsapp_token}"

    def external_endpoint (self, bot_number_id: str) -> str:
        """
        Returns the external endpoint.

        :param bot_number_id: The bot number ID.
        :return: The external endpoint.
        """
        return f"{self.endpoint}/{self.api_version}/{bot_number_id}/messages"

    async def send_message (self, message: dict[str, Any], bot_number_id: str):
        """
        Sends a message.

        :param message: Message (from object) as dict
        :param bot_number_id: Bot number ID
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
        Handles incoming messages from META or ignores

        :param request: Request object
        :raises UnknownEvent: When not a META API event
        :return: A dict with status ='ok' if POST else verify token
        """
        if request.method == "GET":
            return self.webhook_verify_token(request)

        elif request.method == "POST":
            data = request.json
            if data.get("object") is None:
                raise UnknownEvent("Not a META API event.")

            for entry in data["entry"]:
                whatsapp_incoming_update = WhatsappChanges(**entry)

                for change in whatsapp_incoming_update.changes:
                    self.enqueue_update(Incoming.from_dict(change["value"]))

            return { "status": "ok" }

        logging.error(f"This method ({request}) is not allowed here, sorry cowboy.")

    def add_new_state (
        self, state: USER_STATE, on_state_func: Callable,
        handler_trigger: str | MessageTypes | STATE_TRIGGERS
    ):
        """
        Adds a new state to the bot.

        :param state: state name
        :param on_state_func: function to handle state
        :param handler_trigger: triggers for state
        :raises UnknownEvent: When don't reache any trigger
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

        :param state: State name
        :param on_invalid_state_func: function to handle state
        :raises UnknownEvent: If state are not valid
        """
        if state not in self._state_handlers:
            raise UnknownEvent(f"{state} is not a valid state")

        self._state_handlers[state].invalid_state = on_invalid_state_func

    def webhook_verify_token (self, request: Request) -> str:
        """
        Verifies webhook token

        :param request: Incoming request
        :raises MissingParameters: If required parameters are missing
        :raises VerificationFailed: If verify token are different from META API sends
        :return: String challenge
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
        Creates a Flask app for bot

        :param config: Flask config, defaults to None
        :return: Flask app
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

        :param host: Server host, defaults to "127.0.0.1"
        :param port: Server port, defaults to 8000
        :param debug: Flask hot reload and other features, defaults to False
        :param load_dot_env: Loads .env file, defaults to False
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
        Runs bot forever

        :param interval: Interval to verify new incomings, defaults to 0.1
        :raises EmptyState: If bot are empty of states
        """
        logger.info("Starting updater Event")
        if self._initial_state is None:
            raise EmptyState("No states are defined for the bot")

        while True:
            try:
                time.sleep(interval)
                incoming_update = self.get_update()

                if incoming_update is None:
                    continue

                incoming_update = Incoming.from_json(incoming_update)

                await self.process_update(incoming_update)

            except KeyboardInterrupt:
                break

            except Exception:
                logger.error(f"Unknown error: {traceback.format_exc()}")

    def enqueue_update (self, update: Incoming):
        """
        Enqueues an update, change this if you want to use a different queue (like redis).

        :param update: Incoming message
        """
        self._server_queue.put(update.to_json())

    def get_update (self) -> Incoming | None:
        """
        Gets an update from the queue (In-memory, mongodb, redis etc).

        :return: Incoming message
        """
        return self._server_queue.get()

    async def process_update (self, incoming: Incoming):
        """
        Handle updates popped from queue.

        :param incoming: Incoming message
        :raises UnknownEvent: If state are not in state handlers
        """
        for message_idx in range(len(incoming.messages)):
            incoming._message_idx = message_idx

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
