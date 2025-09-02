import json
import time
from typing import Any, Dict, Optional

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # Lazy error if not installed


class KiwoomRestClient:
    """
    Minimal Kiwoom REST API client.

    - Acquires and caches OAuth token using appkey/secretkey
    - Sends JSON requests with required headers: api-id, authorization
    - Supports pagination headers: cont-yn, next-key

    Note:
    - Base URL comes from Kiwoom REST doc: https://api.kiwoom.com
    - Mock base: https://mockapi.kiwoom.com
    - For each API call, you must provide the correct `api_id` and `url_path`.
      You can generate a mapping from restapi.txt using `parse_restapi_doc.py`.
    """

    def __init__(
        self,
        appkey: str,
        secretkey: str,
        use_mock: bool = False,
        base_url: str = "https://api.kiwoom.com",
        mock_base_url: str = "https://mockapi.kiwoom.com",
        session: Optional[Any] = None,
    ) -> None:
        if requests is None:
            raise RuntimeError(
                "The 'requests' package is required. Install with: pip install requests"
            )
        self.appkey = appkey
        self.secretkey = secretkey
        self.base_url = mock_base_url if use_mock else base_url
        self._session = session or requests.Session()
        self._token: Optional[str] = None
        self._token_expire_ts: Optional[float] = None

    # -------------------- OAuth --------------------
    def _token_valid(self) -> bool:
        return bool(self._token) and bool(self._token_expire_ts) and time.time() < (self._token_expire_ts or 0)

    def get_token(self, force: bool = False) -> str:
        if not force and self._token_valid():
            return str(self._token)

        url = f"{self.base_url}/oauth2/token"
        headers = {"Content-Type": "application/json;charset=UTF-8", "api-id": "au10001"}
        body = {"grant_type": "client_credentials", "appkey": self.appkey, "secretkey": self.secretkey}
        resp = self._session.post(url, headers=headers, data=json.dumps(body), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Expected keys per doc: token_type, token, expires_dt (YYYYMMDDhhmmss)
        token_type = data.get("token_type", "Bearer")
        access_token = data.get("token")
        if not access_token:
            raise RuntimeError(f"Token response missing 'token': {data}")

        self._token = access_token if token_type.lower() == "bearer".lower() else f"{token_type} {access_token}"

        expires_dt = data.get("expires_dt")
        # Default to 1 hour if parsing fails
        ttl_seconds = 3600
        if isinstance(expires_dt, str) and len(expires_dt) == 14:
            # When server and client are roughly in sync, use a safety margin
            # We don't parse timezone; just use TTL margin.
            ttl_seconds = 50 * 60
        self._token_expire_ts = time.time() + ttl_seconds
        return str(self._token)

    # -------------------- Generic request --------------------
    def request(
        self,
        api_id: str,
        url_path: str,
        method: str = "POST",
        body: Optional[Dict[str, Any]] = None,
        cont_yn: Optional[str] = None,
        next_key: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        token = self.get_token()
        url = f"{self.base_url}{url_path}"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {token}" if not str(token).lower().startswith("bearer") else str(token),
            "api-id": api_id,
        }
        if cont_yn:
            headers["cont-yn"] = cont_yn
        if next_key:
            headers["next-key"] = next_key
        if extra_headers:
            headers.update(extra_headers)

        m = method.upper()
        if m == "GET":
            resp = self._session.get(url, headers=headers, timeout=timeout)
        else:
            resp = self._session.post(url, headers=headers, data=json.dumps(body or {}), timeout=timeout)
        resp.raise_for_status()

        # Capture pagination headers if present
        result: Dict[str, Any] = {}
        try:
            result = resp.json()
        except Exception:
            result = {"raw": resp.text}

        # Attach response headers for pagination
        for h in ("cont-yn", "next-key"):
            if h in resp.headers:
                result.setdefault("_headers", {})[h] = resp.headers[h]
        return result

    # -------------------- Convenience helpers --------------------
    def call_by_id(
        self,
        api_id: str,
        mapping: Dict[str, str],
        body: Optional[Dict[str, Any]] = None,
        method: str = "POST",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Looks up `url_path` from a mapping (api_id -> url_path) and performs request.
        See parse_restapi_doc.py to generate mapping from restapi.txt.
        """
        if api_id not in mapping:
            raise KeyError(f"api_id {api_id} not found in mapping")
        return self.request(api_id=api_id, url_path=mapping[api_id], method=method, body=body, **kwargs)

