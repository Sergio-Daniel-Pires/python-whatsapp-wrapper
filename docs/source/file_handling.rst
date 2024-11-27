File Handling
=============

This section explains how to handle file uploads, downloads, deletions, and retrievals in the WhatsApp API. Follow the steps below to manage media files efficiently.

Receiving Files
---------------
When a user sends a file, the server receives a message in the following format:

.. code-block:: json

    {
        "from": "5519999999999",
        "id": "wamid.HBgNNTUxOTk5NTU4MDYxNxUCAB...CAA==",
        "timestamp": "1732662139",
        "type": "image",
        "image": {
            "mime_type": "image/jpeg",
            "sha256": "SiRnoo+7WnTnsEXE9s1uQ1RuaE=",
            "id": "1960400821096079"
        }
    }

Retrieve Media Info
To process the file, you first need to retrieve its metadata using the media ID. Use the method :py:meth:`whatsapp.file_handler.retrieve_media_info` to get information about the file, such as its URL. The URL is valid for **5 minutes**, so ensure you download the file promptly.

Download the File
After retrieving the media info, download the file using the provided URL. Ensure your server is capable of handling different file types based on the supported MIME types.

Deleting Files
--------------
If you no longer need a file stored on the WhatsApp server, you can delete it using the method :py:meth:`whatsapp.file_handler.delete_media`.

You will need:
 - The `media_id` of the file.
 - The bearer token that was used to upload the file.

Uploading Files
---------------
To send a file to a user on WhatsApp, it is possible to include a direct `link`  in the message. However, this is **not recommended**. Instead, you should upload the file to the WhatsApp server for better compatibility.

Use method :py:meth:`whatsapp.file_handler.upload_media` to upload a file. Ensure the following:
 - Use the correct MIME type for the file you are uploading.
 - Refer to the list of available MIME types in the :ref:`supported_formats` section.

.. _supported_formats:

Supported Formats
-----------------

The following formats are supported for uploading and sending files via WhatsApp:

Audio Formats
~~~~~~~~~~~~~
- **AAC**: `audio/aac` (.aac, 16 MB)
- **AMR**: `audio/amr` (.amr, 16 MB)
- **MP3**: `audio/mpeg` (.mp3, 16 MB)
- **MP4 Audio**: `audio/mp4` (.m4a, 16 MB)
- **OGG Audio (OPUS codecs only)**: `audio/ogg` (.ogg, 16 MB)

Document Formats
~~~~~~~~~~~~~~~~
- **Text**: `text/plain` (.txt, 100 MB)
- **Microsoft Excel (.xls)**: `application/vnd.ms-excel` (.xls, 100 MB)
- **Microsoft Excel (.xlsx)**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (.xlsx, 100 MB)
- **Microsoft Word (.doc)**: `application/msword` (.doc, 100 MB)
- **Microsoft Word (.docx)**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (.docx, 100 MB)
- **Microsoft PowerPoint (.ppt)**: `application/vnd.ms-powerpoint` (.ppt, 100 MB)
- **Microsoft PowerPoint (.pptx)**: `application/vnd.openxmlformats-officedocument.presentationml.presentation` (.pptx, 100 MB)
- **PDF**: `application/pdf` (.pdf, 100 MB)

Image Formats
~~~~~~~~~~~~~
- **JPEG**: `image/jpeg` (.jpeg, 5 MB)
- **PNG**: `image/png` (.png, 5 MB)

Sticker Formats
~~~~~~~~~~~~~~~
- **Animated Sticker (WebP)**: `image/webp` (.webp, 500 KB)
- **Static Sticker (WebP)**: `image/webp` (.webp, 100 KB)

Video Formats
~~~~~~~~~~~~~
- **3GPP**: `video/3gp` (.3gp, 16 MB)
- **MP4 Video**: `video/mp4` (.mp4, 16 MB)
