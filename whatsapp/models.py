import dataclasses as dc
import logging
from typing import Any, Literal, TypeVar

from whatsapp.message import MSG_TYPE_TO_OBJECT, IncomingMessage

USER_STATE = TypeVar("USER_STATE", str, int)


@dc.dataclass
class Metadata:
    display_phone_number: str = dc.field()
    "Phone number that cusomer will see in chat"
    phone_number_id: str = dc.field()
    "Phone number id. Need to be used to respond an message "

    def to_json (self):
        self.__dict__

@dc.dataclass
class Contacts:
    wa_id: str = dc.field()
    "Customer whatsapp ID (Can match customer phone number or not)"
    profile: dict[str, Any] = dc.field()
    "Customer profile object (today has only name)"

    @property
    def customer_name (self):
        """
        Customer's name
        """
        return self.profile["name"]

    def to_json (self):
        self.__dict__

@dc.dataclass
class Errors:
    code: int = dc.field()
    "Error code. Example: '130429'"
    title: str = dc.field()
    "Error code title. Example: 'Rate limit hit'"
    message: str = dc.field()
    "Error code with title. Example: '(#130429) Rate limit hit'"
    error_data: dict[str, Any] = dc.field()

    @property
    def error_details(self):
        """
        Describes the error
        """
        return self.error_data["details"]

    def to_json (self):
        self.__dict__

CONVERSATION_CATEGORY = Literal["authentication", "marketing", "utility", "service", "referral_conversion"]

@dc.dataclass
class Conversation:
    """
    Information about the conversation
    """
    id: str = dc.field()
    "Conversation ID"
    origin: dict[str, str] = dc.field()
    "Conversation category"
    expiration_timestamp: int = dc.field()
    "Date when the conversation expires"

    @property
    def origin_type (self) -> CONVERSATION_CATEGORY:
        """
        Convesation category (or entry point)

        authentication: The conversation was opened by a business sending a 'AUTHENTICATION'

        marketing: The conversation was opened by a business sending a 'MARKETING'

        utility: The conversation was opened by a business sending a 'UTILITY'

        service: The conversation opened by a business replying to a customer within a customer service window

        referral_conversion: Indicates a free entry point conversation
        """
        return self.origin["type"]

@dc.dataclass
class Pricing:
    category: CONVERSATION_CATEGORY = dc.field()
    "Conversation category"
    pricing_model: Literal["CBP"] = dc.field()
    "Pricing model type"
    billable: bool = dc.field(default=None)
    "False if it's a free message entry point"

@dc.dataclass
class Statuses:
    """
    Triggered when a message are sent/delivered to a customer
    or the customer reads the delivered message
    """
    id: str = dc.field()
    "Message ID"
    status: Literal["delivered", "read", "sent"] = dc.field()
    """
    Message status

    delivered: Webhook received when message was delivered

    read: Webhook received when customer reads the message

    sent: Webhook received when a business sends a message
    """
    timestamp: int = dc.field()
    "Message status Date"
    recipient_id: str = dc.field()
    "Customer's WhatsApp ID. Can be used to respond a customer (Doesn't match with phone number)"
    biz_opaque_callback_data: str = dc.field(default=None)
    "Arbitrary string"
    conversation: Conversation = dc.field(default=None)
    "Conversation info"
    errors: list[Errors] = dc.field(default_factory=list)
    "List of objects describing errors"
    pricing: Pricing = dc.field(default=None)
    "Pricing information"

    def __post_init__ (self):
        self.errors = [ Errors(**error) for error in self.errors ]

        if self.pricing is not None:
            self.pricing = Pricing(**self.pricing)

    def to_json (self):
        output = { **self.__dict__ }

        output["error"] = [ error.to_json() for error in self.errors ]

        if isinstance(self.pricing, dict):
            output["pricing"] = self.pricing.__dict__

        return output

@dc.dataclass
class Incoming:
    messaging_product: Literal["whatsapp"] = dc.field()
    "Product used to send the message. (Always whatsap)"
    metadata: Metadata = dc.field()
    "Business account webhook metadata"
    contacts: list[Contacts] = dc.field(default_factory=list)
    errors: list[Errors] = dc.field(default_factory=list)
    messages: list[IncomingMessage] = dc.field(default_factory=list)
    statuses: list[Statuses] = dc.field(default_factory=list)

    def __post_init__ (self):
        self.metadata = Metadata(**self.metadata)
        self.contacts = [ Contacts(**contact) for contact in self.contacts ]
        self.errors = [ Errors(**error) for error in self.errors ]
        self.statuses = [ Statuses(**status) for status in self.statuses ]

        converted_messages = []

        for message in self.messages:
            msg_type = message["type"]
            msg_object = MSG_TYPE_TO_OBJECT.get(msg_type)

            if msg_object is None:
                logging.error(f"Message {msg_type} are not implemented yet.")
                continue
            
            # TODO remove this manual fix
            if "from" in message:
                message["from_"] = message.pop("from")

            converted_messages.append(msg_object(**message))

        self.messages = converted_messages

    def to_send (self):
        output = {
            "messaging_product": self.messaging_product, "metadata": self.metadata.to_json()
        }

        for attr_key in ( "contacts", "errors", "statuses" ):
            attr_value: list[Contacts | Errors | Statuses] = getattr(self, attr_key, None)

            if attr_value is None:
                continue

            output[attr_key] = [ attr.to_json() for attr in attr_value ]

        return output

@dc.dataclass
class IncomingPayload:
    id: str
    "Whatsapp business ID"
    changes: list[Incoming]
    "Changed objects array"

    def __post_init__ (self):
        self.changes = [ Incoming(**change["value"]) for change in self.changes ]
