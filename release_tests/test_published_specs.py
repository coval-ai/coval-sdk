"""Exercise publication verification with real HTTP and unchanged-file controls."""

import copy
import hashlib
import http.server
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error


ROOT = Path(__file__).resolve().parents[1]


class TestPublishedSpecs(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "published_specs", ROOT / "scripts/fetch-published-specs.py"
        )
        self.consumer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.consumer)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.destination = Path(self.temporary.name) / "specs"
        self.destination.mkdir()
        (self.destination / "old-v1.yaml").write_bytes(b"previous publication")
        (self.destination / "keep.md").write_bytes(b"unmanaged documentation")
        self.bodies = {
            "agents": b"openapi: 3.0.0\ninfo: {title: Agents}\n",
            "alerts": b"openapi: 3.0.0\ninfo: {title: Alerts}\n",
        }
        self.requests = []
        bodies, requests = self.bodies, self.requests

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                name = self.path.rsplit("/", 1)[-1]
                requests.append((name, self.headers.get("Authorization")))
                self.send_response(200 if name in bodies else 404)
                self.end_headers()
                self.wfile.write(bodies.get(name, b"missing"))

            def log_message(self, *_):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}
        )
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.consumer.BASE_URL = (
            f"http://127.0.0.1:{self.server.server_port}/v1/openapi"
        )
        self.event = {
            "client_payload": {
                "schema_version": 1,
                "ref": "a" * 40,
                "specs": [
                    {"name": name, "sha256": hashlib.sha256(body).hexdigest()}
                    for name, body in self.bodies.items()
                ],
            }
        }

    def stop_server(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def files(self):
        return {
            path.name: path.read_bytes() for path in self.destination.iterdir()
        }

    def test_verified_manifest_replaces_only_managed_specs_without_credentials(
        self,
    ):
        self.assertEqual(
            self.consumer.download(self.event, self.destination), "a" * 40
        )
        self.assertEqual(
            self.files(),
            {
                "agents-v1.yaml": self.bodies["agents"],
                "alerts-v1.yaml": self.bodies["alerts"],
                "keep.md": b"unmanaged documentation",
            },
        )
        self.assertEqual(self.requests, [("agents", None), ("alerts", None)])

    def test_later_mismatch_preserves_every_previous_input(self):
        before = self.files()
        self.bodies["alerts"] = b"a newer publication"
        with self.assertRaisesRegex(
            self.consumer.PublicationError, "rerun the backend"
        ):
            self.consumer.download(self.event, self.destination)
        self.assertEqual(self.files(), before)
        self.assertEqual(
            [name for name, _ in self.requests], ["agents", "alerts"]
        )

    def test_missing_later_resource_preserves_every_previous_input(self):
        before = self.files()
        del self.bodies["alerts"]
        with self.assertRaises(urllib.error.HTTPError) as raised:
            self.consumer.download(self.event, self.destination)
        raised.exception.close()
        self.assertEqual(self.files(), before)

    def test_invalid_complete_manifest_is_rejected_before_any_request(self):
        before = self.files()
        cases = [
            {},
            {"schema_version": True},
            {"ref": "main"},
            {"specs": []},
            {"specs": [{"name": "../private", "sha256": "b" * 64}]},
            {"specs": [{"name": "agents", "sha256": "invalid"}]},
            {"specs": [self.event["client_payload"]["specs"][0]] * 2},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                event = copy.deepcopy(self.event)
                if overrides:
                    event["client_payload"].update(overrides)
                else:
                    del event["client_payload"]["schema_version"]
                with self.assertRaises(self.consumer.PublicationError):
                    self.consumer.download(event, self.destination)
                self.assertEqual(self.requests, [])
                self.assertEqual(self.files(), before)


if __name__ == "__main__":
    unittest.main()
