import logging
import re
import traceback
from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any

from flask import jsonify

from whatsapp.error import MissingParameters, UnknownEvent, VerificationFailed


def middleware (f: Callable):
    @wraps(f)
    def _middleware (*args, **kwargs):
            try:
                result = f(*args, **kwargs)

            except MissingParameters as exc:
                return jsonify({ "status": "error", "message": exc.message }), 403

            except ( VerificationFailed, UnknownEvent ) as exc:
                return jsonify({ "status": "error", "message": exc.message }), 400

            except Exception as exc:
                logging.error(traceback.format_exc())
                return jsonify({ "status": "error", "message": str(exc) }), 500

            # Converts python dict-like to json response
            if isinstance(result, ( Mapping, dict )):
                result = jsonify(result)

            return result, 200

    return _middleware
