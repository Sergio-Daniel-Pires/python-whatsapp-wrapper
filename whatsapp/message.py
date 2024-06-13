import dataclasses as dc
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Literal, TypeVar

from dataclasses_json import config, dataclass_json

USER_STATE = TypeVar("USER_STATE", str, int)
CONVERSATION_CATEGORY = Literal["authentication", "marketing", "utility", "service", "referral_conversion"]

class MessageTypes (str, Enum):
    ADDRESS: str = "address"
    AUDIO: str = "audio"
    CONTACTS: str = "contacts"
    DOCUMENT: str = "document"
    IMAGE: str = "image"
    INTERACTIVE: str = "interactive"
    FLOW: str = "flow"
    LOCATION: str = "location"
    REACTION: str = "reaction"
    STICKER: str = "sticker"
    TEMPLATE: str = "template"
    TEXT: str = "text"
    VIDEO: str = "video"

@dc.dataclass
class InteractiveButtonItem:
    id: str = dc.field()
    title: str = dc.field()

@dc.dataclass
class SectionItem:
    id: str = dc.field()
    title: str = dc.field()
    description: str = dc.field()

@dc.dataclass
class Section:
    title: str = dc.field()
    rows: list[SectionItem] = dc.field(default_factory=list)

    def __post_init__ (self):
        self.rows = [
            row if isinstance(row, SectionItem) else SectionItem(**row) for row in self.rows
        ]

@dataclass_json
@dc.dataclass
class Context:
    from_: str = dc.field(metadata=config(field_name="from"))
    "Customer whatsapp number"
    id: str = dc.field()
    "Message id (Used for replies for example.)"

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

@dataclass_json
@dc.dataclass
class ReceivedMessage (ABC):
    id: str = dc.field()
    "Message id (Used for replies for example.)"
    timestamp: str = dc.field()
    "Unix timestamp"
    type: MessageTypes = dc.field()
    "Message Type (Specified in MessageTypes)"
    from_: str = dc.field(metadata=config(field_name="from"))
    "Customer whatsapp number"
    context: Context = dc.field(default=None)
    "Context object, if customer has replied a message"

    def __post_init__ (self):
        if self.type in ( MessageTypes.TEXT, ):
            if not self.text:
                raise ValueError("For TEXT type, 'text' must be provided in MessageHeaderValue.")

        elif self.type in ( MessageTypes.DOCUMENT, ):
            if not (self.id or self.link):
                raise ValueError(
                    "For DOCUMENT type, either 'id' or 'link'"
                    "must be provided in MessageHeaderValue."
                )

        elif self.type in ( MessageTypes.VIDEO, MessageTypes.IMAGE ):
            if not (self.id or self.link):
                raise ValueError(
                    f"For {str(self.type).upper()} type, either 'id' or 'link'"
                    "must be provided in MessageHeaderValue."
                )

            # TODO fix filename for images
            # if self.filename:
            #     raise ValueError(
            #         f"For {str(self.type).upper()} type, 'filename' is not supported."
            #     )

        if self.context is not None:
            self.context = Context.from_dict(self.context)

    @classmethod
    def default_body_to_reply (
        cls, to: str, msg_type: MessageTypes, context: Context | dict[str, str] = None,
    ) -> dict[str, Any]:
        default_body = {
            "messaging_product": "whatsapp", "type": msg_type,
            "recipient_type": "individual", "to": to
        }

        if context is not None:
            default_body["context"] = context if isinstance(context, dict) else context.to_json()

        return default_body

    @classmethod
    @abstractmethod
    def to_reply (cls, to: str, *args, **kwargs) -> dict[str, str]:
        ...


@dataclass_json
@dc.dataclass
class Incoming:
    messaging_product: Literal["whatsapp"] = dc.field()
    "Product used to send the message. (Always whatsap)"
    metadata: Metadata = dc.field()
    "Business account webhook metadata"
    contacts: list[Contacts] = dc.field(default_factory=list)
    "Information about who sents the message"
    errors: list[Errors] = dc.field(default_factory=list)
    "Objects that describes errors"
    messages: list[ReceivedMessage] = dc.field(default_factory=list)
    "Triggered when a customer updates their profile information or sends a message"
    statuses: list[Statuses] = dc.field(default_factory=list)
    "Triggered when a message is sent or delivered to a customer or he reads the message"

    _message_idx: int = dc.field(default=0)
    "Message index that will be handled now"

    def __post_init__ (self):
        self.metadata = Metadata(**self.metadata)
        self.contacts = [ Contacts(**contact) for contact in self.contacts ]
        self.errors = [ Errors(**error) for error in self.errors ]
        self.statuses = [ Statuses(**status) for status in self.statuses ]

        converted_messages = []

        for message in self.messages:
            msg_type = message["type"]
            msg_object = RECEIVED_MSG_TYPE_TO_OBJECT.get(msg_type)

            if msg_object is None:
                logging.error(f"Message {msg_type} are not implemented yet.")
                continue

            # TODO remove this manual fix
            if "from" in message:
                message["from_"] = message.pop("from")

            converted_messages.append(msg_object(**message))

        self.messages = converted_messages

    @property
    def message (self) -> ReceivedMessage:
        "Message that will be handled now (Selected by _message_idx)"
        return self.messages[self._message_idx] if self.messages else None

    @message.setter
    def message (self, value: ReceivedMessage):
        raise ValueError("Can't set message directly. Use '_message_idx' instead.")

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
class WhatsappChanges:
    id: str
    "Whatsapp business ID"
    changes: list[Incoming]
    "Changed objects array"

    def __post_init__ (self):
        self.changes = [ Incoming(**change["value"]) for change in self.changes ]

@dataclass_json
@dc.dataclass
class AddressMessage (ReceivedMessage):
    """
    Handle ask address messages
    """
    ...

@dataclass_json
@dc.dataclass
class AudioMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class ContactMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class DocumentMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class ImageMessage (ReceivedMessage):
    image: dict[str, str] = dc.field(kw_only=True)
    link: str = dc.field(default=None, kw_only=True)
    caption: str = dc.field(default=None, kw_only=True)

    @classmethod
    def to_reply (
        cls, to: str, image_id: str = None, link: str = None, caption: str = None
    ) -> dict[str, str]:
        if image_id is None and link is None:
            raise ValueError("media_id and media_link can't be both None.")

        output_msg = cls.default_body_to_reply(to, MessageTypes.IMAGE)

        if image_id:
            output_msg["id"] = image_id

        if link:
            output_msg["link"] = link

        if caption:
            output_msg["caption"] = caption

        return output_msg

class ButtonUrlMessage (ReceivedMessage):
    ...

class FlowMessage (ReceivedMessage):
    # TODO Implement FlowMessage when I receive API access
    ...

@dataclass_json
@dc.dataclass
class InteractiveListMessage:
    header: str = dc.field(kw_only=True)
    body: str = dc.field(kw_only=True)
    footer: str = dc.field(kw_only=True)
    button_title: str = dc.field(kw_only=True)

    sections: list[Section] = dc.field(kw_only=True)

    def __post_init__ (self):
        self.sections = [
            section if isinstance(section, Section) else Section(**section)
            for section in self.sections
        ]

    def to_reply (self, to: str) -> dict[str, str]:
        return {
            **ReceivedMessage.default_body_to_reply(to, MessageTypes.INTERACTIVE),
            "interactive": {
                "type": "list",
                "header": { "type": "text", "text": self.header },
                "body": { "text": self.body },
                "footer": { "text": self.footer },
                "action": {
                    "button": self.button_title,
                    "sections": [ section.to_json() for section in self.sections ]
                }
            }
        }

@dataclass_json
@dc.dataclass
class InteractiveListReply (ReceivedMessage):
    interactive: dict[str, str] = dc.field(kw_only=True)

    @property
    def message_value (self) -> str:
        return f"{self.list_reply.title}\n{self.list_reply.description}"

    @property
    def list_reply(self) -> SectionItem:
        return SectionItem(**self.interactive["list_reply"])

    @list_reply.setter
    def list_reply(self, value: SectionItem):
        raise ValueError("Can't set list_reply directly. Use 'interactive' instead.")

    @classmethod
    def to_reply (cls, to: str, *args, **kwargs):
        raise ValueError(
            "'InteractiveListReply' can't be used to send messages. "
            "Use 'InteractiveListMessage' instead."
        )

@dataclass_json
@dc.dataclass
class ReplyButtonsMessage:
    header: str = dc.field(kw_only=True) # TODO add support for emoji, markdown etc
    body: str = dc.field(kw_only=True)
    footer: str = dc.field(kw_only=True)

    buttons: list[InteractiveButtonItem] = dc.field(kw_only=True)

    def __post_init__ (self):
        self.sections = [
            section if isinstance(section, Section) else Section(**section)
            for section in self.sections
        ]

    def to_reply (self, to: str,) -> dict[str, str]:
        return {
            **ReceivedMessage.default_body_to_reply(to, MessageTypes.INTERACTIVE),
            "interactive": {
                "type": "button",
                "header": { "type": "text", "text": self.header },
                "body": { "text": self.body },
                "footer": { "text": self.footer },
                "action": {
                    "buttons": [
                        { "type": "reply", "reply": button.to_json() } for button in self.buttons
                    ]
                }
            }
        }

@dataclass_json
@dc.dataclass
class ReplyButtonsReply (ReceivedMessage):
    interactive: dict[str, str] = dc.field(kw_only=True)

    button_reply: SectionItem = dc.field(init=False)

    @property
    def message_value (self) -> str:
        return f"{self.button_reply.title}\n{self.button_reply.description}"

    @property
    def button_reply(self) -> SectionItem:
        return SectionItem(**self.interactive["button_reply"])

    @button_reply.setter
    def button_reply(self, value: SectionItem):
        raise ValueError("Can't set button_reply directly. Use 'interactive' instead.")

    @classmethod
    def to_reply (cls, to: str, *args, **kwargs):
        raise ValueError(
            "'InteractiveListReply' can't be used to send messages. "
            "Use 'InteractiveListMessage' instead."
        )

@dataclass_json
@dc.dataclass
class LocationMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class AskForLocationMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class ReactMessage (ReceivedMessage):
    reaction: dict[str, str] = dc.field(kw_only=True)
    message_id: str = dc.field(kw_only=True)
    emoji: str = dc.field(kw_only=True)

    @classmethod
    def to_reply (
        cls, to: str, message_id: str, emoji: str
    ) -> dict[str, str]:
        output_msg = cls.default_body_to_reply(to, MessageTypes.REACTION)
        output_msg["reaction"] = { "message_id": message_id, "emoji": emoji }

        return output_msg

@dataclass_json
@dc.dataclass
class StickerMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class TextMessage (ReceivedMessage):
    text: dict[str, str] = dc.field(kw_only=True)
    "Dict that contains message value"

    @property
    def message_value (self) -> str:
        return self.text["body"]

    @classmethod
    def to_reply (cls, to: str, message: str, preview_url: bool = None) -> dict[str, str]:
        output_msg = cls.default_body_to_reply(to, MessageTypes.TEXT)
        output_msg["text"] = { "body": message }

        if preview_url is not None:
            output_msg["text"]["preview_url"] = True

        return output_msg

@dataclass_json
@dc.dataclass
class VideoMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class ReadMessage (ReceivedMessage):
    ...

RECEIVED_MSG_TYPE_TO_OBJECT: dict[str, ReceivedMessage] = {
    MessageTypes.TEXT: TextMessage, MessageTypes.REACTION: ReactMessage,
    MessageTypes.IMAGE: ImageMessage, MessageTypes.INTERACTIVE: InteractiveListReply
}

