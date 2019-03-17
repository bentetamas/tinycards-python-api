import json
import os
from requests_toolbelt.multipart.encoder import MultipartEncoder


CARDS = 'cards'
IMAGE_FILE = 'imageFile'
BLACKLISTED_QUESTION_TYPES = 'blacklistedQuestionTypes'
GRADING_MODES = 'gradingModes'
TTS_LANGUAGES = 'ttsLanguages'
# Keys for which the data needs to be JSON-encoded:
JSON_KEYS = set([CARDS, BLACKLISTED_QUESTION_TYPES, GRADING_MODES, TTS_LANGUAGES])
# Keys for which the data needs to be encoded in special ways:
SPECIAL_KEYS = set([IMAGE_FILE]).union(JSON_KEYS)


def to_multipart_form(data, boundary=None):
    """Create a multipart form like produced by HTML forms from a dict."""
    fields = {}
    for k, v in data.items():
        if k not in SPECIAL_KEYS:
            fields[k] = str(v) if not isinstance(v, bool) else str(v).lower()
        if k in JSON_KEYS:
            fields[k] = json.dumps(data[k])
    if has_image_file(data):
        # See also: https://toolbelt.readthedocs.io/en/latest/uploading-data.html#uploading-data
        fields[IMAGE_FILE] = ('cover.jpg', open(data[IMAGE_FILE], 'rb'), 'image/jpeg')
    return MultipartEncoder(fields=fields, boundary=boundary)


def has_image_file(data):
    return IMAGE_FILE in data and data[IMAGE_FILE] and os.path.exists(data[IMAGE_FILE])
