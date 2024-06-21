from typing import Any

import pytest

# from whatsapp.message import AudioMessage, Incoming, TextMessage, ContactMessage, DocumentMessage, ImageMessage, InteractiveListReply, InteractiveButtonsReply, LocationMessage, ReactMessage, TextMessage, VideoMessage
from whatsapp.message import (AudioMessage, DocumentMessage, ImageMessage,
                              Incoming, LocationMessage, ReactMessage,
                              TextMessage)


@pytest.mark.parametrize(
    [ "context" ], [ ( None, ), ( { "from": "5519990000000", "id": "wamid.Hbg==" }, ) ]
)
class TestReceiveValidMessage:
    """
    All tests in this class should receive an payload with message text and if is an url
    """
    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_address_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "audio" ],
        [ ( {
            "mime_type": "audio/ogg; codecs=opus",
            "sha256": "0JvAKM3QpqS6B0dJ+JVHkDLMgfXJ1xkdeceKWlHtJjk=",
            "id": "48310", "voice": True
        }, ) ]
    )
    async def test_audio_message (
        self, default_user_incoming: dict[str, Any], default_message: dict[str, str],
        audio: dict[str, str], context: None | dict[str, str]
    ):
        # Add audio message to the default message
        default_message["context"] = context
        default_message.update({ "type": "audio", "audio": audio })

        default_user_incoming["messages"].append(default_message)

        incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.message is not None, "Message is None"
        assert isinstance(incoming.message, AudioMessage), "Wrong Message Type"

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_contact_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "document" ],
        [ ( {
            "filename": "document.pdf",
            "mime_type": "application/pdf",
            "sha256": "RbuM08btWYx573le2kdGGg7aAr5lPiqXxST9MdLpTTU",
            "id": "48773"
        }, ) ]
    )
    async def test_document_message (
        self, default_user_incoming: dict[str, Any], default_message: dict[str, str],
        document: dict[str, str], context: None | dict[str, str]
    ):
        # Add document message to the default message
        default_message["context"] = context
        default_message.update({ "type": "document", "document": document })

        default_user_incoming["messages"].append(default_message)

        incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.message is not None, "Message is None"
        assert isinstance(incoming.message, DocumentMessage), "Wrong Message Type"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "image" ],
        [ ( {
            "mime_type": "image/jpeg",
            "sha256": "RbuM08btWYx573le2kdGGg7aAr5lPiqXxST9MdLpTTU",
            "id": "48773"
        }, ) ]
    )
    async def test_image_message (
        self, default_user_incoming: dict[str, Any], default_message: dict[str, str],
        image: dict[str, str], context: None | dict[str, str]
    ):
        # Add image message to the default message
        default_message["context"] = context
        default_message.update({ "type": "image", "image": image })

        default_user_incoming["messages"].append(default_message)

        incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.message is not None, "Message is None"
        assert isinstance(incoming.message, ImageMessage), "Wrong Message Type"

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemeted yet")
    async def test_button_url_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_flow_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_interactive_list_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_interactive_button_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "location" ],
        [ ( {
            "address": "Faria Lima, SP - Brazil",
            "latitude": -23.577240015985964, "longitude": -46.686841903982845,
            "name": "Job", "url": "https://foursquare.com/v/57d8607bcd105224c7efa925"
        }, ) ]
    )
    async def test_location_message (
        self, default_user_incoming: dict[str, Any], default_message: dict[str, str],
        location: dict[str, str], context: None | dict[str, str]
    ):
        # Add location message to the default message
        default_message["context"] = context
        default_message.update({ "type": "location", "location": location })

        default_user_incoming["messages"].append(default_message)

        incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.message is not None, "Message is None"
        assert isinstance(incoming.message, LocationMessage), "Wrong Message Type"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "reaction" ],
        [ ( {
            "message_id": "wamid.HBgNNTUAA==", "emoji": "\ud83d\udc4d"
        }, ) ]
    )
    async def test_react_message (
        self, default_user_incoming: dict[str, Any], default_message: dict[str, str],
        reaction: dict[str, str], context: None | dict[str, str]
    ):
        # Add location message to the default message
        default_message["context"] = context
        default_message.update({ "type": "reaction", "reaction": reaction })

        default_user_incoming["messages"].append(default_message)

        incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.message is not None, "Message is None"
        assert isinstance(incoming.message, ReactMessage), "Wrong Message Type"

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_sticker_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "message_text", "is_url" ],
        [ ( "Hello World!", False ), ( "https://github.com.br", True ) ]
    )
    async def test_text_message (
        self, default_user_incoming: dict[str, Any], default_message: dict[str, str],
        message_text: str, is_url: bool, context: None | dict[str, str]
    ):
        # Add text message to the default message
        default_message["context"] = context
        default_message.update({ "type": "text", "text": { "body": message_text } })
        if is_url:
            default_message["text"]["preview_url"] = is_url

        default_user_incoming["messages"].append(default_message)

        incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.message is not None, "Message is None"
        assert isinstance(incoming.message, TextMessage), "Wrong Message Type"

        assert incoming.message.message_value == message_text

    @pytest.mark.asyncio
    @pytest.mark.skip("Not implemented yet")
    async def test_video_message (self, context: None | dict[str, str]):
        ...

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        [ "statuses" ],
        [ ( [ {
            "id": "wamid.Hbg2RAA==", "status": "sent", "timestamp": "1631610000",
            "recipient_id": "51999", 
            "conversation": {
                "id": "wacnvo.1", "expiration_timestamp": "1631610000",
                "origin": { "type": "service" }
            },
            "pricing": { "billable": True, "pricing_model": "CBP", "category": "service" }
        } ], ) ]
    )
    async def test_pricing_message (
        self, default_user_incoming: dict[str, str], statuses: dict[str, Any],
        context: None | dict[str, str]
    ):
        default_user_incoming["statuses"] = statuses

        incoming: Incoming = Incoming.from_dict(default_user_incoming)

        assert incoming.status.pricing is not None

        assert incoming.status.conversation is not None
        assert incoming.status.conversation.origin_type == "service"
