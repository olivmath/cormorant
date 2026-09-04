"""LiveKit credentials and short-lived room token generation."""

from datetime import timedelta

from livekit import api

from src.config import settings
from src.schemas import LiveKitTokenResponse

ROOM_NAME = "cormorant-mvp"
_IDENTITIES = {"publisher": "mobile-camera", "viewer": "admin-dashboard", "worker": "counter-worker"}


def configured() -> bool:
    return bool(settings.livekit_url and settings.livekit_api_key and settings.livekit_api_secret)


def create_room_token(role: str) -> LiveKitTokenResponse:
    if role not in _IDENTITIES:
        raise ValueError("Unknown LiveKit role")
    can_publish = role == "publisher"
    token = (
        api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(_IDENTITIES[role])
        .with_ttl(timedelta(minutes=15))
        .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME, can_publish=can_publish,
                                     can_subscribe=not can_publish, can_publish_data=False,
                                     hidden=role == "worker"))
        .to_jwt()
    )
    return LiveKitTokenResponse(server_url=settings.livekit_url, token=token, room=ROOM_NAME)
