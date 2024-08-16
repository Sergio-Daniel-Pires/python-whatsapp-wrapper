import logging
import traceback
from collections.abc import Callable, Mapping
from functools import wraps

from flask import jsonify

from whatsapp.error import MissingParameters, UnknownEvent, VerificationFailed


def middleware(f: Callable):
    """
    Decorator for normalize responses, handle exceptions.

    :param f: View function
    :return: Decorated function
    """
    @wraps(f)
    def _middleware(*args, **kwargs):
        try:
            result = f(*args, **kwargs)

        except MissingParameters as exc:
            return jsonify({" status": "error", "message": exc.message }), 403

        except (VerificationFailed, UnknownEvent) as exc:
            return jsonify({ "status": "error", "message": exc.message }), 400

        except Exception as exc:
            logging.error(traceback.format_exc())
            return jsonify({ "status": "error", "message": str(exc) }), 500

        # Converts python dict-like to json response
        if isinstance(result, Mapping):
            result = jsonify(result)

        return result, 200

    return _middleware
