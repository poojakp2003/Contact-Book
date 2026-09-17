"""Local browser application for the contact book."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from main import ContactBook


ROOT = Path(__file__).parent
HOST = "127.0.0.1"
PORT = 8000


class ContactRequestHandler(BaseHTTPRequestHandler):
    """Serve the contact dashboard and a small JSON API."""

    book = ContactBook()

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self._serve_file(ROOT / "templates" / "index.html", "text/html; charset=utf-8")
        elif parsed_url.path == "/static/app.js":
            self._serve_file(ROOT / "static" / "app.js", "text/javascript; charset=utf-8")
        elif parsed_url.path == "/static/styles.css":
            self._serve_file(ROOT / "static" / "styles.css", "text/css; charset=utf-8")
        elif parsed_url.path == "/api/contacts":
            params = parse_qs(parsed_url.query)
            query = params.get("q", [""])[0].strip()
            group_filter = params.get("group", [""])[0].strip()
            favorite_filter = params.get("favorite", [""])[0].strip().lower() == "true"

            try:
                self.book.load()
                contacts = self.book.contacts

                if group_filter and group_filter.lower() != "all":
                    contacts = self.book.filter_by_group(group_filter)

                if favorite_filter:
                    contacts = [c for c in contacts if c.get("favorite", False) is True]

                if query:
                    clean_query = query.casefold()
                    contacts = [
                        c for c in contacts
                        if any(clean_query in str(val).casefold() for val in c.values())
                    ]

                sorted_contacts = sorted(contacts, key=lambda c: c["name"].casefold())
                self._send_json(200, sorted_contacts)
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/contacts/favorite":
            contact_name = parse_qs(parsed_url.query).get("name", [""])[0]
            if not contact_name:
                self._send_json(400, {"error": "Contact name is required"})
                return
            try:
                self.book.load()
                toggled = self.book.toggle_favorite(contact_name)
                self.book.save()
                self._send_json(200, toggled)
            except (ValueError, RuntimeError) as error:
                self._send_json(400, {"error": str(error)})
            return

        if parsed_url.path != "/api/contacts":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            contact = self._read_json()
            created = self.book.add(
                name=contact.get("name", ""),
                phone=contact.get("phone", ""),
                email=contact.get("email", ""),
                address=contact.get("address", ""),
                group=contact.get("group", "Other"),
                favorite=bool(contact.get("favorite", False)),
            )
            self.book.save()
            self._send_json(201, created)
        except (ValueError, KeyError, json.JSONDecodeError, RuntimeError) as error:
            self._send_json(400, {"error": str(error)})

    def do_PUT(self) -> None:
        contact_name = self._contact_name()
        if contact_name is None:
            return
        try:
            contact = self._read_json()
            updated = self.book.update(
                contact_name,
                phone=contact.get("phone", ""),
                email=contact.get("email", ""),
                address=contact.get("address", ""),
                group=contact.get("group", "Other"),
                favorite=contact.get("favorite"),
                new_name=contact.get("name", contact_name),
            )
            self.book.save()
            self._send_json(200, updated)
        except (ValueError, KeyError, json.JSONDecodeError, RuntimeError) as error:
            self._send_json(400, {"error": str(error)})

    def do_DELETE(self) -> None:
        contact_name = self._contact_name()
        if contact_name is None:
            return
        try:
            deleted = self.book.delete(contact_name)
            self.book.save()
            self._send_json(200, deleted)
        except (ValueError, RuntimeError) as error:
            self._send_json(404, {"error": str(error)})

    def _contact_name(self) -> str | None:
        name = parse_qs(urlparse(self.path).query).get("name", [""])[0]
        if not name:
            self._send_json(400, {"error": "Contact name is required"})
            return None
        return name

    def _read_json(self) -> dict[str, str]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("Request body must be an object")
        return data

    def _serve_file(self, path: Path, content_type: str) -> None:
        try:
            content = path.read_bytes()
        except OSError:
            self._send_json(404, {"error": "File not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: int, payload: object) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def run_server() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ContactRequestHandler)
    print(f"Contact Book is running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Contact Book.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
