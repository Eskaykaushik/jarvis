import json
import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)

_signing_key = None


def _get_signing_key():
    global _signing_key
    if _signing_key is not None:
        return _signing_key

    raw = settings.supabase_jwt_secret
    if not raw:
        raise RuntimeError("SUPABASE_JWT_SECRET is not configured")

    if raw.strip().startswith("{"):
        jwk_set = json.loads(raw)
        keys = jwk_set.get("keys", [jwk_set])
        jwk_data = keys[0]
        _signing_key = jwt.PyJWK(jwk_data)
    else:
        _signing_key = jwt.PyJWK.from_dict({"k": raw, "kty": "oct", "alg": "HS256"})

    return _signing_key


def get_current_user_id(request: Request) -> str | None:
    """Extract and verify the JWT from the Authorization header.

    Returns the user_id from the Supabase JWT payload, or None if
    no token was provided. Raises HTTPException if a token is present
    but invalid/expired.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[len("Bearer "):].strip()

    try:
        signing_key = _get_signing_key()
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            audience=settings.supabase_url,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )

    request.state.user_id = user_id
    return user_id


CurrentUser = Annotated[str | None, Depends(get_current_user_id)]


def require_user(user_id: CurrentUser = None) -> str:
    """Dependency that enforces authentication — raises 401 if no valid user."""
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


AuthenticatedUser = Annotated[str, Depends(require_user)]
