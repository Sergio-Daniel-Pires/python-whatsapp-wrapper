import io
import logging

import httpx

from whatsapp.bot import WhatsappBot

logger = logging.getLogger(__name__)

MB = 1024 * 1024


async def send_whatsapp_business_encryption (
    bot_number_id: str, bot: WhatsappBot, public_key: str
) -> dict:
    """
    Sends a POST request to the WhatsApp Business Encryption endpoint with the business public key.
    Used for whatsapp flows

    :param phone_number_id: The phone number ID for the WhatsApp Business account.
    :param access_token: The access token for authenticating with the WhatsApp Business API.
    :param business_public_key: The public key to register with the WhatsApp Business encryption.
    :return: The response JSON from the API.
    """
    url = bot.external_endpoint(bot_number_id, "whatsapp_business_encryption")
    headers = {
        "Authorization": bot.bearer_token, "Content-Type": "application/x-www-form-urlencoded"
    }
    data = { "business_public_key": public_key }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)

        response.raise_for_status()

    return response.json()

async def get_whatsapp_business_encryption (bot_number_id: str, bot: WhatsappBot) -> dict:
    """
    Sends a GET request to retrieve WhatsApp Business Encryption information.

    :param phone_number_id: The phone number ID for the WhatsApp Business account.
    :param access_token: The access token for authenticating with the WhatsApp Business API.
    :return: The response JSON from the API.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            bot.external_endpoint(bot_number_id, "whatsapp_business_encryption"),
            headers={ "Authorization": bot.bearer_token }
        )

        response.raise_for_status()

    return response.json()

async def upload_media(
    bot: WhatsappBot, bot_number_id: str, file_data: bytes | io.BytesIO, media_type: str
) -> dict[str, str]:
    """
    Uploads media to WhatsApp Business.

    :param bot: The WhatsappBot instance with access token and API endpoint information.
    :param bot_number_id: The bot number ID for the WhatsApp Business account.
    :param file_path: Path to the file to be uploaded.
    :param media_type: The MIME type of the file (e.g., "image/jpeg").

    Supported file formats, MIME types, and size limitations:

    Audio Formats:
        - AAC: audio/aac (.aac, 16 MB)
        - AMR: audio/amr (.amr, 16 MB)
        - MP3: audio/mpeg (.mp3, 16 MB)
        - MP4 Audio: audio/mp4 (.m4a, 16 MB)
        - OGG Audio: audio/ogg (OPUS codecs only; base audio/ogg not supported) (.ogg, 16 MB)

    Document Formats:
        - Text: text/plain (.txt, 100 MB)
        - Microsoft Excel (.xls): application/vnd.ms-excel (.xls, 100 MB)
        - Microsoft Excel (.xlsx): application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (.xlsx, 100 MB)
        - Microsoft Word (.doc): application/msword (.doc, 100 MB)
        - Microsoft Word (.docx): application/vnd.openxmlformats-officedocument.wordprocessingml.document (.docx, 100 MB)
        - Microsoft PowerPoint (.ppt): application/vnd.ms-powerpoint (.ppt, 100 MB)
        - Microsoft PowerPoint (.pptx): application/vnd.openxmlformats-officedocument.presentationml.presentation (.pptx, 100 MB)
        - PDF: application/pdf (.pdf, 100 MB)

    Image Formats:
        - JPEG: image/jpeg (.jpeg, 5 MB)
        - PNG: image/png (.png, 5 MB)

    Sticker Formats:
        - Animated Sticker (WebP): image/webp (.webp, 500 KB)
        - Static Sticker (WebP): image/webp (.webp, 100 KB)

    Video Formats:
        - 3GPP: video/3gp (.3gp, 16 MB)
        - MP4 Video: video/mp4 (.mp4, 16 MB)

    :return: The response JSON with the media ID.
    """
    MAX_FILE_SIZE_TO_UPLOAD = 100 * MB

    # Calculate file size
    if isinstance(file_data, bytes):
        file_size = len(file_data)

    elif hasattr(file_data, 'seek') and hasattr(file_data, 'tell'):
        current_position = file_data.tell()
        file_data.seek(0, 2)
        file_size = file_data.tell()
        file_data.seek(current_position)

    else:
        raise TypeError("file_data must be of type bytes or a file-like object supporting seek and tell.")

    if file_size > MAX_FILE_SIZE_TO_UPLOAD:
        logger.warning(
            "The maximum supported file size for media messages on Cloud API is 100MB. "
        )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            bot.external_endpoint(bot_number_id, "media"),
            headers={ "Authorization": bot.bearer_token },
            data={ "messaging_product": "whatsapp", "type": media_type },
            files={ "file": ("uploaded_file", file_data, media_type) }
        )

        response.raise_for_status()

    return response.json()

async def retrieve_media_info (bot: WhatsappBot, media_id: str) -> dict:
    """
    Retrieves the URL for a specific media item.

    :param bot: The WhatsappBot instance with access token and API endpoint information.
    :param media_id: The ID of the media item.
    :return: The response JSON with the media URL and metadata.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            bot.external_endpoint(media_id, ""), headers={ "Authorization": bot.bearer_token }
        )

        response.raise_for_status()

    return response.json()

async def delete_media (bot: WhatsappBot, media_id: str) -> dict:
    """
    Deletes a specific media item.

    :param bot: The WhatsappBot instance with access token and API endpoint information.
    :param media_id: The ID of the media item to delete.
    :return: The response JSON indicating success.
    """

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            bot.external_endpoint(media_id, ""), headers={ "Authorization": bot.bearer_token }
        )

        response.raise_for_status()

    return response.json()

async def download_media (bot: WhatsappBot, media_url: str) -> bytes:
    """
    Downloads media from a given media URL.

    :param bot: The WhatsappBot instance with access token and API endpoint information.
    :param media_url: The URL for the media file to download.
    :return: The binary content of the downloaded media file.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(media_url, headers={ "Authorization": bot.bearer_token })

        response.raise_for_status()

    return response.content
