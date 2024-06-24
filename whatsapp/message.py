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

@dataclass_json
@dc.dataclass
class InteractiveButtonItem:
    id: str = dc.field()
    title: str = dc.field()

@dataclass_json
@dc.dataclass
class SectionItem:
    id: str = dc.field()
    title: str = dc.field()
    description: str = dc.field()

@dataclass_json
@dc.dataclass
class Section:
    title: str = dc.field()
    rows: list[SectionItem] = dc.field(default_factory=list)

@dataclass_json
@dc.dataclass
class DocumentMetadata:
    mime_type: str = dc.field()
    sha256: str = dc.field()
    id: str = dc.field()
    filename: str | None = dc.field(default=None)
    "Exclusive for document media"
    voice: bool | None = dc.field(default=None, kw_only=True)
    "Exclusive for voice/audio media"
    animated: bool | None = dc.field(default=None, kw_only=True)
    "Exclusive for sticker media"

@dataclass_json
@dc.dataclass
class Reaction:
    message_id: str = dc.field()
    emoji: str = dc.field()

@dataclass_json
@dc.dataclass
class Location:
    latitude: float = dc.field()
    "Location latitude in decimal degrees."
    longitude: float = dc.field()
    "Location longitude in decimal degrees."
    address: str | None = dc.field(default=None)
    "location address (Optional)"
    name: str | None = dc.field(default=None)
    "location name (Optional)"
    url: str | None = dc.field(default=None)
    "Location guide url (Optional)"

@dataclass_json
@dc.dataclass
class Context:
    from_: str = dc.field(metadata=config(field_name="from"))
    "Customer whatsapp number"
    id: str = dc.field()
    "Message id (Used for replies for example.)"

@dataclass_json
@dc.dataclass
class Metadata:
    display_phone_number: str = dc.field()
    "Phone number that cusomer will see in chat"
    phone_number_id: str = dc.field()
    "Phone number id. Need to be used to respond an message "

@dataclass_json
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

@dataclass_json
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

@dataclass_json
@dc.dataclass
class Conversation:
    """
    Information about the conversation
    """
    id: str = dc.field()
    "Conversation ID"
    origin: dict[str, str] = dc.field()
    "Conversation category"
    expiration_timestamp: str | None = dc.field(default=None)
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

@dataclass_json
@dc.dataclass
class Pricing:
    category: CONVERSATION_CATEGORY = dc.field()
    "Conversation category"
    pricing_model: Literal["CBP"] = dc.field()
    "Pricing model type"
    billable: bool = dc.field(default=None)
    "False if it's a free message entry point"

@dataclass_json
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
    biz_opaque_callback_data: str | None = dc.field(default=None)
    "Arbitrary string"
    conversation: Conversation = dc.field(default=None)
    "Conversation info"
    errors: list[Errors] = dc.field(default_factory=list)
    "List of objects describing errors"
    pricing: Pricing = dc.field(default=None)
    "Pricing information"

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
    context: Context | None = dc.field(default=None)
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

    @classmethod
    def default_body_to_send (
        cls, to: str, msg_type: MessageTypes, context: Context | dict[str, str] = None,
    ) -> dict[str, Any]:
        default_body = {
            "messaging_product": "whatsapp", "type": msg_type,
            "recipient_type": "individual", "to": to
        }

        if context is not None:
            default_body["context"] = context.to_json()

        return default_body

    @classmethod
    @abstractmethod
    def to_send (cls, to: str, *args, **kwargs) -> dict[str, str]:
        ...

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
    audio: DocumentMetadata = dc.field(kw_only=True)
    link: str | None = dc.field(default=None, kw_only=True)
    caption: str | None = dc.field(default=None, kw_only=True)

    @classmethod
    def to_send (
        cls, to: str, audio_id: str = None, link: str = None
    ) -> dict[str, str]:
        output_msg = cls.default_body_to_send(to, MessageTypes.AUDIO)

        if audio_id:
            output_msg["id"] = audio_id

        elif link:
            output_msg["link"] = link

        else:
            raise ValueError("Either 'audio_id' or 'link' must be provided.")

        return output_msg

    @property
    def audio_id (self) -> str:
        return self.audio.id

    @audio_id.setter
    def audio_id (self, value: str):
        raise ValueError("Can't set 'audio_id' directly. Use 'audio.id' instead.")

@dataclass_json
@dc.dataclass
class ContactMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class DocumentMessage (ReceivedMessage):
    document: DocumentMetadata = dc.field(kw_only=True)

    @classmethod
    def to_send (
        cls, to: str, document_id: str = None, link: str = None,
        caption: str = None, filename: str = None
    ) -> dict[str, str]:
        output_msg = cls.default_body_to_send(to, MessageTypes.DOCUMENT)

        if document_id:
            output_msg["id"] = document_id

        elif link:
            output_msg["link"] = link

        else:
            raise ValueError("Either 'document_id' or 'link' must be provided.")

        if caption:
            output_msg["caption"] = caption

        if filename:
            output_msg["filename"] = filename

        return output_msg

    @property
    def filename (self) -> str:
        return self.document.filename

    @filename.setter
    def filename (self, value: str):
        raise ValueError("Can't set 'filename' directly. Use 'document.filename' instead.")

@dataclass_json
@dc.dataclass
class ImageMessage (ReceivedMessage):
    image: DocumentMetadata = dc.field(kw_only=True)
    link: str | None = dc.field(default=None, kw_only=True)
    caption: str | None = dc.field(default=None, kw_only=True)

    @classmethod
    def to_send (
        cls, to: str, image_id: str = None, link: str = None, caption: str = None
    ) -> dict[str, str]:
        output_msg = cls.default_body_to_send(to, MessageTypes.IMAGE)

        if image_id:
            output_msg["id"] = image_id

        elif link:
            output_msg["link"] = link

        else:
            raise ValueError("Either 'image_id' or 'link' must be provided.")

        if caption:
            output_msg["caption"] = caption

        return output_msg

    @property
    def image_id (self) -> str:
        return self.image.id

    @image_id.setter
    def image_id (self, value: str):
        raise ValueError("Can't set 'image_id' directly. Use 'image.id' instead.")

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

    def to_send (self, to: str) -> dict[str, str]:
        return {
            **ReceivedMessage.default_body_to_send(to, MessageTypes.INTERACTIVE),
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
        return SectionItem.from_dict(self.interactive["list_reply"])

    @list_reply.setter
    def list_reply(self, value: SectionItem):
        raise ValueError("Can't set list_reply directly. Use 'interactive' instead.")

    @classmethod
    def to_send (cls, to: str, *args, **kwargs):
        raise ValueError(
            "'InteractiveListReply' can't be used to send messages. "
            "Use 'InteractiveListMessage' instead."
        )

@dataclass_json
@dc.dataclass
class InteractiveButtonsMessage:
    header: str = dc.field(kw_only=True) # TODO add support for emoji, markdown etc
    body: str = dc.field(kw_only=True)
    footer: str = dc.field(kw_only=True)

    buttons: list[InteractiveButtonItem] = dc.field(kw_only=True)

    def to_send (self, to: str,) -> dict[str, str]:
        return {
            **ReceivedMessage.default_body_to_send(to, MessageTypes.INTERACTIVE),
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
class InteractiveButtonsReply (ReceivedMessage):
    interactive: dict[str, str] = dc.field(kw_only=True)

    button_reply: SectionItem = dc.field(init=False)

    @property
    def message_value (self) -> str:
        return f"{self.button_reply.title}\n{self.button_reply.description}"

    @property
    def button_reply(self) -> SectionItem:
        return SectionItem.from_dict(self.interactive["button_reply"])

    @button_reply.setter
    def button_reply(self, value: SectionItem):
        raise ValueError("Can't set button_reply directly. Use 'interactive' instead.")

    @classmethod
    def to_send (cls, to: str, *args, **kwargs):
        raise ValueError(
            "'InteractiveListReply' can't be used to send messages. "
            "Use 'InteractiveListMessage' instead."
        )

@dataclass_json
@dc.dataclass
class LocationMessage (ReceivedMessage):
    location: Location = dc.field(kw_only=True)

    @classmethod
    def to_send(
        cls, to: str, latitude: str, longitude: str, address: str = None, name: str = None
    ):
        output_msg = cls.default_body_to_send(to, MessageTypes.LOCATION)
        output_msg["location"] = { "latitude": latitude, "longitude": longitude }

        if address:
            output_msg["location"]["address"] = address

        if name:
            output_msg["location"]["name"] = name

        return output_msg

@dataclass_json
@dc.dataclass
class AskForLocationMessage (ReceivedMessage):
    ...

@dataclass_json
@dc.dataclass
class ReactMessage (ReceivedMessage):
    reaction: Reaction = dc.field(kw_only=True)

    @classmethod
    def to_send (
        cls, to: str, message_id: str, emoji: str
    ) -> dict[str, str]:
        output_msg = cls.default_body_to_send(to, MessageTypes.REACTION)
        output_msg["reaction"] = { "message_id": message_id, "emoji": emoji }

        return output_msg

@dataclass_json
@dc.dataclass
class StickerMessage (ReceivedMessage):
    sticker: DocumentMetadata = dc.field(kw_only=True)

    @classmethod
    def to_send (
        cls, to: str, sticker_id: str = None, link: str = None,
        caption: str = None
    ) -> dict[str, str]:
        output_msg = cls.default_body_to_send(to, MessageTypes.DOCUMENT)

        if sticker_id:
            output_msg["id"] = sticker_id

        elif link:
            output_msg["link"] = link

        else:
            raise ValueError("Either 'sticker_id' or 'link' must be provided.")

        return output_msg

    @property
    def animated (self) -> bool:
        return self.sticker.animated

    @animated.setter
    def animated (self, value: str):
        raise ValueError("Can't set 'animated' directly. Use 'sticker.id' instead.")

@dataclass_json
@dc.dataclass
class TextMessage (ReceivedMessage):
    text: dict[str, str] = dc.field(kw_only=True)
    "Dict that contains message value"

    @property
    def message_value (self) -> str:
        return self.text["body"]

    @classmethod
    def to_send (cls, to: str, message: str, preview_url: bool = None) -> dict[str, str]:
        output_msg = cls.default_body_to_send(to, MessageTypes.TEXT)
        output_msg["text"] = { "body": message }

        if preview_url:
            output_msg["text"]["preview_url"] = True

        return output_msg

@dataclass_json
@dc.dataclass
class VideoMessage (ReceivedMessage):
    """
    Video message. Contains information about sent and received videos.
    """
    video: DocumentMetadata = dc.field(kw_only=True)

    @classmethod
    def to_send (
        cls, to: str, video_id: str = None, link: str = None, caption: str = None
    ) -> dict[str, str]:
        """
        Creates a video reply message.

        :param to: Recipient's phone number.
        :param video_id: Video ID, if available.
        :param link: Video link, if available.
        :param caption: Video caption, if available.
        :return: Dictionary representing the reply message.
        """
        if video_id is None and link is None:
            raise ValueError("video_id and link can't both be None.")

        output_msg = cls.default_body_to_send(to, MessageTypes.VIDEO)

        if video_id:
            output_msg["video"] = { "id": video_id }

        if link:
            output_msg["video"] = { "link": link }

        if caption:
            output_msg["video"]["caption"] = caption

        return output_msg

@dataclass_json
@dc.dataclass
class ReadMessage (ReceivedMessage):
    ...

MESSAGE_TYPE = TypeVar("MESSAGE_TYPE", TextMessage, ReactMessage)

RECEIVED_MSG_TYPE_TO_OBJECT: dict[str, ReceivedMessage] = {
    MessageTypes.AUDIO: AudioMessage,
    MessageTypes.ADDRESS: AddressMessage,
    MessageTypes.CONTACTS: ContactMessage,
    MessageTypes.DOCUMENT: DocumentMessage,
    MessageTypes.IMAGE: ImageMessage,
    MessageTypes.INTERACTIVE: InteractiveListReply,
    MessageTypes.FLOW: FlowMessage,
    MessageTypes.LOCATION: LocationMessage,
    MessageTypes.REACTION: ReactMessage,
    MessageTypes.STICKER: StickerMessage,
    MessageTypes.TEXT: TextMessage,
    MessageTypes.VIDEO: VideoMessage
}

def map_received_msg_to_obj (messages: list[dict[str, Any]] | None):
    if messages is None:
        return []

    try:
        converted_messages = []

        for message in messages:
            msg_type = message["type"]
            msg_object = RECEIVED_MSG_TYPE_TO_OBJECT.get(msg_type)

            if msg_object is None:
                raise Exception(f"Message type '{msg_type}' not supported.")

            converted_messages.append(msg_object.from_dict(message))

        return converted_messages

    except Exception as exc:
        logging.error("Error while converting messages to objects.", exc_info=exc)
        return []

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
    messages: list[ReceivedMessage] = dc.field(
        metadata=config(decoder=map_received_msg_to_obj), default_factory=list
    )
    "Triggered when a customer updates their profile information or sends a message"
    statuses: list[Statuses] = dc.field(default_factory=list)
    "Triggered when a message is sent or delivered to a customer or he reads the message"

    _message_idx: int = dc.field(default=0)
    "Message index that will be handled now"

    _status_idx: int = dc.field(default=0)
    "Status index that will be handled now"

    @property
    def message (self) -> ReceivedMessage:
        "Message that will be handled now (Selected by _message_idx)"
        return self.messages[self._message_idx] if self.messages else None

    @message.setter
    def message (self, value: ReceivedMessage):
        raise ValueError("Can't set message directly. Use '_message_idx' instead.")

    @property
    def status (self) -> Statuses:
        "Status that will be handled now (Selected by _status_idx)"
        return self.statuses[self._status_idx] if self.statuses else None

    @status.setter
    def status (self, value: Statuses):
        raise ValueError("Can't set message directly. Use '_status_idx' instead.")

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

@dataclass_json
@dc.dataclass
class WhatsappChanges:
    id: str
    "Whatsapp business ID"
    changes: list[Incoming]
    "Changed objects array"
