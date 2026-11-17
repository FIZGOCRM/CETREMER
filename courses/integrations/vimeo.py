"""Optional Vimeo metadata lookup; failure must not prevent editing a lesson."""

import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def video_duration(url):
    if urlparse(url).hostname not in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        return 0
    endpoint = "https://vimeo.com/api/oembed.json?" + urlencode({"url": url})
    try:
        with urlopen(endpoint, timeout=5) as response:
            return max(0, int(json.load(response).get("duration") or 0))
    except (URLError, OSError, ValueError, TypeError, AttributeError):
        logger.warning("Não foi possível consultar a duração do vídeo no Vimeo.")
        return 0
