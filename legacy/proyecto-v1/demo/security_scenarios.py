"""Escenarios seguros de defensa; solo admite destinos loopback."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def request(base: str, path: str, source: str, method: str = "GET", agent: str = "demo-defensiva/1.0") -> int:
    data = b"usuario=demo&clave=no-es-un-secreto" if method == "POST" else None
    item = Request(
        base.rstrip("/") + path,
        data=data,
        method=method,
        headers={"User-Agent": agent, "X-Demo-Source": source, "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlopen(item, timeout=5) as response:
            return response.status
    except HTTPError as error:
        return error.code


def run(base: str) -> dict[str, object]:
    host = urlparse(base).hostname
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("La demo solo puede ejecutarse contra loopback")
    results: dict[str, object] = {"normal": request(base, "/", "normal")}
    results["sqli"] = request(base, "/?id=1%20UNION%20SELECT%20demo", "sqli")
    results["xss"] = request(base, "/?q=%3Cscript%3Edemo%3C/script%3E", "xss")
    results["user_agent"] = request(base, "/", "ua", agent="sqlmap-demo")
    brute = [request(base, "/login", "brute", "POST") for _ in range(5)]
    results["brute_force"] = brute[-1]
    scan = [request(base, path, "scan") for path in ("/admin", "/backup", "/config", "/private", "/old", "/test", "/debug")]
    results["route_scan"] = scan[-1]
    flood = [request(base, "/", "flood") for _ in range(31)]
    results["http_flood"] = flood[-1]
    expected = {"normal": 200, "sqli": 403, "xss": 403, "user_agent": 403, "brute_force": 403, "route_scan": 403, "http_flood": 429}
    results["passed"] = all(results[key] == value for key, value in expected.items())
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    arguments = parser.parse_args()
    outcome = run(arguments.url)
    print(json.dumps(outcome, indent=2, ensure_ascii=False))
    raise SystemExit(0 if outcome["passed"] else 1)
