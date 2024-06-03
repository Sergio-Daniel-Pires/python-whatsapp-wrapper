import dataclasses as dc
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class MessageTypes (str, Enum):
    TEXT: str = "text"
    REACTION: str = "reaction"
    IMAGE: str = "image"
    LOCATION: str = "location"
    CONTACTS: str = "contacts"
    INTERACTIVE: str = "interactive"
    TEMPLATE: str = "template"
    FLOW: str = "flow"

    # Headers Types
    DOCUMENT: str = "document"
    VIDEO: str = "video"

@dc.dataclass()
class IncomingMessage (ABC):
    id: str = dc.field()
    timestamp: str = dc.field()
    type: MessageTypes = dc.field()
    from_: str = dc.field()
    context: dict[str, Any] = dc.field(default=None)

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

            if self.filename:
                raise ValueError(
                    f"For {str(self.type).upper()} type, 'filename' is not supported."
                )

    @classmethod
    def default_body_reply (cls, to: str, msg_type: MessageTypes) -> dict[str, Any]:
        return {
            "messaging_product": "whatsapp", "type": msg_type,
            "recipient_type": "individual", "to": to
        }

    @classmethod
    @abstractmethod
    def to_reply (cls, to: str, *args, **kwargs):
        ...

@dc.dataclass
class TextMessage (IncomingMessage):
    text: dict[str, str] = dc.field(kw_only=True)
    "Dict that contains message value"

    @property
    def message_value (self) -> str:
        return self.text["body"]

    @classmethod
    def to_reply (cls, to: str, message: str, preview_url: bool = None) -> dict[str, str]:
        output_msg = cls.default_body_reply(to, MessageTypes.TEXT)
        output_msg["text"] = { "body": message }

        if preview_url is not None:
            output_msg["text"]["preview_url"] = True

        return output_msg

@dc.dataclass
class ReactMessage (IncomingMessage):
    reaction: dict[str, str] = dc.field(kw_only=True)
    message_id: str = dc.field(kw_only=True)
    emoji: str = dc.field(kw_only=True)

    @classmethod
    def to_reply (
        cls, to: str, message_id: str, emoji: str
    ) -> dict[str, str]:
        output_msg = cls.default_body_reply(to, MessageTypes.REACTION)
        output_msg["reaction"] = { "message_id": message_id, "emoji": emoji }

        return output_msg

@dc.dataclass
class ImageMessage (IncomingMessage):
    image: dict[str, str] = dc.field(kw_only=True)
    from_: str = dc.field()
    id: str = dc.field(default=None, kw_only=True)
    link: str = dc.field(default=None, kw_only=True)
    caption: str = dc.field(default=None, kw_only=True)

    @classmethod
    def to_reply (
        cls, to: str, image_id: str = None, link: str = None, caption: str = None
    ) -> dict[str, str]:
        if image_id is None and link is None:
            raise ValueError("media_id and media_link can't be both None.")

        output_msg = cls.default_body_reply(to, MessageTypes.IMAGE)
        
        if image_id:
            output_msg["id"] = image_id

        if link:
            output_msg["link"] = link

        if caption:
            output_msg["caption"] = caption

        return output_msg

@dc.dataclass()
class SectionItem:
    id: str = dc.field()
    title: str = dc.field()
    description: str = dc.field()

@dc.dataclass()
class Section:
    title: str = dc.field()
    rows: list[SectionItem] = dc.field(default_factory=list)

    def __post_init__ (self):
        self.rows = [
            row if isinstance(row, SectionItem) else SectionItem(**row) for row in self.rows
        ]

    def to_json (self) -> dict[str, str]:
        return { "title": self.title, "rows": [ row.__dict__ for row in self.rows ] }

@dc.dataclass
class InteractiveListMessage (IncomingMessage):
    interactive: dict[str, str] = dc.field(kw_only=True)
    from_: str = dc.field()
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

    @classmethod
    def to_reply (
        cls, to: str, header: str, body: str, footer: str,
        button_title: str, sections: list[Section]
    ) -> dict[str, str]:
        return {
            **cls.default_body_reply(to, MessageTypes.INTERACTIVE),
            "interactive": {
                "type": "list",
                "header": { "type": "text", "text": header },
                "body": { "text": body },
                "footer": { "text": footer },
                "action": {
                    "button": button_title,
                    "sections": [
                        section.to_json() if isinstance(section, Section) else section
                        for section in sections
                    ]
                }
            }
        }

@dc.dataclass
class InteractiveListReply:
    id: str = dc.field()
    timestamp: str = dc.field()
    type: MessageTypes = dc.field()
    from_: str = dc.field()
    context: dict[str, Any] = dc.field(default=None)
    interactive: dict[str, str] = dc.field(kw_only=True)

    list_reply: SectionItem = dc.field(init=False)

    def __post_init__ (self):
        self.list_reply = SectionItem(**self.interactive["list_reply"])

    @property
    def message_value (self) -> str:
        return f"{self.list_reply.title}\n{self.list_reply.description}"

class FlowMessage (IncomingMessage):
    ...

MSG_TYPE_TO_OBJECT: dict[str, IncomingMessage] = {
    MessageTypes.TEXT: TextMessage, MessageTypes.REACTION: ReactMessage,
    MessageTypes.IMAGE: ImageMessage, MessageTypes.INTERACTIVE: InteractiveListReply
}
