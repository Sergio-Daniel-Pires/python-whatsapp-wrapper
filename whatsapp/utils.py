import logging
import traceback
from collections.abc import Callable, Mapping
from functools import wraps

from flask import jsonify

from whatsapp.error import MissingParameters, UnknownEvent, VerificationFailed


def middleware(f: Callable):
    """
    A decorator function that acts as middleware for error handling and response formatting.

    Args:
        f (Callable): The function to be decorated.

    Returns:
        Callable: The decorated function.

    Raises:
        MissingParameters: If the decorated function raises a MissingParameters exception, it returns a JSON response with a 403 status code.
        VerificationFailed: If the decorated function raises a VerificationFailed exception, it returns a JSON response with a 400 status code.
        UnknownEvent: If the decorated function raises an UnknownEvent exception, it returns a JSON response with a 400 status code.
        Exception: If the decorated function raises any other exception, it returns a JSON response with a 500 status code.
    """
    @wraps(f)
    def _middleware(*args, **kwargs):
        """
        Middleware function that handles exceptions and converts the result to a JSON response.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Tuple: A tuple containing the result and the HTTP status code.

        Raises:
            MissingParameters: If required parameters are missing.
            VerificationFailed: If verification fails.
            UnknownEvent: If an unknown event occurs.
            Exception: If any other exception occurs.
        """
        try:
            result = f(*args, **kwargs)

        except MissingParameters as exc:
            return jsonify({"status": "error", "message": exc.message}), 403

        except (VerificationFailed, UnknownEvent) as exc:
            return jsonify({"status": "error", "message": exc.message}), 400

        except Exception as exc:
            logging.error(traceback.format_exc())
            return jsonify({"status": "error", "message": str(exc)}), 500

        # Converts python dict-like to json response
        if isinstance(result, ( Mapping, dict )):
            result = jsonify(result)

        return result, 200

    return _middleware
