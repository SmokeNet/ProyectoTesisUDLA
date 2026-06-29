"""Cliente HTTP comun para componentes internos."""

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ApiClientError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if method != "GET":
            if not self.api_key:
                raise ApiClientError("API_WRITE_KEY no configurada")
            headers["X-API-Key"] = self.api_key
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ApiClientError(str(error)) from error

    def create_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/api/v1/events", payload)

    def create_metric(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/api/v1/metrics", payload)

    def heartbeat(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/api/v1/heartbeat", payload)

    def create_evidence(self, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", f"/api/v1/events/{event_id}/evidence", payload)

    def create_remediation(self, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", f"/api/v1/events/{event_id}/remediations", payload)
