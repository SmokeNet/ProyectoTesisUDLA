"""Sondas sinteticas y de infraestructura."""

import hashlib
import os
import socket
import ssl
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import psutil
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .config import Settings
from .domain import Observation


class SyntheticProbe:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.last_screenshot: Path | None = None

    def _network(self, observation: Observation) -> None:
        parsed = urlparse(self.settings.monitored_url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            socket.getaddrinfo(host, port)
            observation.dns_ok = True
        except socket.gaierror as error:
            observation.dns_ok = False
            observation.error_kind = "dns"
            observation.error_detail = str(error)
            return
        try:
            with socket.create_connection((host, port), timeout=5):
                observation.port_open = True
        except OSError as error:
            observation.port_open = False
            observation.error_kind = "service_stopped"
            observation.error_detail = str(error)
        if parsed.scheme == "https":
            try:
                context = ssl.create_default_context()
                with socket.create_connection((host, port), timeout=5) as raw:
                    with context.wrap_socket(raw, server_hostname=host) as secured:
                        certificate = secured.getpeercert()
                expires = datetime.strptime(
                    certificate["notAfter"],
                    "%b %d %H:%M:%S %Y %Z",
                ).replace(tzinfo=timezone.utc)
                observation.ssl_valid = True
                observation.ssl_days_remaining = (expires - datetime.now(timezone.utc)).days
            except (OSError, ssl.SSLError, ValueError, KeyError) as error:
                observation.ssl_valid = False
                observation.error_detail = str(error)

    def _platform(self, observation: Observation) -> None:
        # Una ventana de un segundo evita clasificar picos instantaneos como saturacion.
        observation.cpu_percent = psutil.cpu_percent(interval=1.0)
        observation.memory_percent = psutil.virtual_memory().percent
        observation.disk_percent = psutil.disk_usage(str(Path.cwd().anchor)).percent
        try:
            process = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            observation.docker_ok = process.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            observation.docker_ok = False
        if observation.docker_ok:
            try:
                containers = subprocess.run(
                    [
                        "docker",
                        "compose",
                        "-f",
                        str(self.settings.compose_file),
                        "ps",
                        "--status",
                        "running",
                        "--services",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                running = set(containers.stdout.splitlines())
                observation.container_running = self.settings.service_name in running
            except (OSError, subprocess.TimeoutExpired):
                observation.container_running = None
        max_connections = int(os.getenv("MAX_ESTABLISHED_CONNECTIONS", "1000"))
        if max_connections > 0:
            try:
                established = sum(
                    1
                    for connection in psutil.net_connections(kind="inet")
                    if connection.status == "ESTABLISHED"
                )
                observation.connections_percent = min(100.0, established / max_connections * 100)
            except (psutil.Error, OSError):
                observation.connections_percent = None
        try:
            with urlopen(f"{self.settings.api_base_url}/api/v1/health", timeout=5) as response:
                observation.api_ok = response.status == 200
                body = response.read().decode("utf-8")
                observation.database_ok = '"mysql":"ok"' in body.replace(" ", "")
        except (HTTPError, URLError, TimeoutError):
            observation.api_ok = False
            observation.database_ok = None
        ssh_host = os.getenv("SSH_CHECK_HOST")
        if ssh_host:
            try:
                address = (ssh_host, int(os.getenv("SSH_CHECK_PORT", "22")))
                with socket.create_connection(address, timeout=5) as connection:
                    observation.ssh_ok = connection.recv(32).startswith(b"SSH-")
            except OSError:
                observation.ssh_ok = False

    def _baseline(self, content: str, observation: Observation) -> None:
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        observation.content_hash = digest
        directory = self.settings.evidence_dir / "baselines"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.settings.service_name}.sha256"
        if path.exists():
            observation.content_changed = path.read_text(encoding="ascii").strip() != digest
        else:
            path.write_text(digest, encoding="ascii")
            observation.content_changed = False

    def observe(self) -> Observation:
        observation = Observation(
            service=self.settings.service_name,
            server=self.settings.server_name,
            target=self.settings.monitored_url,
        )
        self.last_screenshot = None
        self._network(observation)
        self._platform(observation)
        if observation.dns_ok is False or observation.port_open is False:
            return observation
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                failed_resources: list[str] = []

                def track_response(response) -> None:
                    critical_types = {"script", "stylesheet", "image", "font"}
                    if response.status >= 400 and response.request.resource_type in critical_types:
                        failed_resources.append(f"{response.status} {response.url}")

                page.on("response", track_response)
                navigation_started = time.perf_counter()
                try:
                    response = page.goto(
                        self.settings.monitored_url,
                        wait_until="domcontentloaded",
                        timeout=self.settings.timeout_ms,
                    )
                    observation.latency_ms = (
                        time.perf_counter() - navigation_started
                    ) * 1000
                    observation.http_status = response.status if response else None
                    body = page.locator("body").inner_text()
                    observation.content_expected = self.settings.expected_text in body
                    observation.critical_resources_ok = not failed_resources
                    observation.metadata["failed_resources"] = failed_resources[:20]
                    self._baseline(body, observation)
                    if observation.http_status and observation.http_status >= 500:
                        observation.error_kind = "application"
                    if not observation.content_expected:
                        observation.error_kind = observation.error_kind or "content"
                except (PlaywrightTimeoutError, PlaywrightError) as error:
                    observation.latency_ms = (
                        time.perf_counter() - navigation_started
                    ) * 1000
                    detail = str(error)
                    observation.error_detail = detail
                    if "Timeout" in detail:
                        observation.error_kind = "timeout"
                    elif "ERR_NAME_NOT_RESOLVED" in detail:
                        observation.error_kind = "dns"
                        observation.dns_ok = False
                    elif "ERR_CONNECTION" in detail:
                        observation.error_kind = "service_stopped"
                        observation.port_open = False
                    else:
                        observation.error_kind = "application"
                    screenshot_dir = self.settings.evidence_dir / "capturas"
                    screenshot_dir.mkdir(parents=True, exist_ok=True)
                    self.last_screenshot = screenshot_dir / f"{self.settings.service_name}_{int(time.time())}.png"
                    page.screenshot(path=str(self.last_screenshot), full_page=True)
                finally:
                    browser.close()
        except PlaywrightError as error:
            observation.error_kind = "application"
            observation.error_detail = f"Playwright no disponible: {error}"
        return observation
