# Contact Book Management System

A command-line contact manager written in Python. Contacts are stored in `contacts.json` so they remain available between sessions.

## Features

- Add, view, search, update, and delete contacts
- JSON-based persistent storage
- Required-field and email validation
- Case-insensitive duplicate-name detection
- Graceful handling of invalid input and corrupt storage

## Run the web app

```powershell
python web_app.py
```

Then open `http://127.0.0.1:8000` in a browser. The web app supports adding, searching, editing, and deleting contacts.

## Run the command-line version

```powershell
python main.py
```

The application creates `contacts.json` in the project folder when the first contact is saved.

## Test

```powershell

```
