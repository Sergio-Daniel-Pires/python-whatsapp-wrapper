import os
import time

import pytest


@pytest.fixture
def customer_number ():
    """
    Get customer number for tests (Default can be set in the environment variable)
    """
    return os.environ.get("PYTEST_CUSTOMER_NUMBER", "5519900000000")

@pytest.fixture
def business_number ():
    """
    Get customer number for tests (Default can be set in the environment variable)
    """
    return os.environ.get("PYTEST_BUSINESS_NUMBER", "5519900000000")

@pytest.fixture
def default_user_incoming (customer_number: str, business_number: str):
    """
    Default incoming message, with a single message that only need to be
    filled up with "type" and type value
    """
    return {
        "messaging_product": "whatsapp",
        "metadata": { "display_phone_number": business_number, "phone_number_id": "1" },
        "contacts": [ { "wa_id": customer_number, "profile": { "name": "Customer" } } ],
        "errors": [],
        "messages": [],
        "statuses": [],
    }

@pytest.fixture
def default_message (customer_number: str):
    return {
        "id": "wamid.messageId==",
        "timestamp": str(int(time.time())),
        "from": customer_number,
        "context": None,
    }

@pytest.fixture
def default_outgoing (customer_number: str):
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": customer_number
    }