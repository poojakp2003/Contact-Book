"""Command-line contact book with JSON persistence, Groups, and Favorites."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("contacts.json")
EMAIL_REGEX = re.compile(r"^[a-z][a-zA-Z0-9_.+-]*@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DEFAULT_GROUPS = ["Family", "Friends", "Work", "College", "Other"]


def validate_name(name: str) -> str:
    """Validate that the contact name is not empty."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Contact name cannot be empty. Please enter a valid name.")
    return clean_name


def validate_phone(phone: str) -> str:
    """Validate that the phone number contains exactly 10 digits (numbers only)."""
    clean_phone = phone.strip()
    if not clean_phone:
        raise ValueError("Phone number cannot be empty. Please enter a 10-digit phone number.")
    if not clean_phone.isdigit():
        if any(c.isalpha() for c in clean_phone):
            raise ValueError("Phone number cannot contain letters. Only numbers are accepted.")
        raise ValueError("Phone number cannot contain special characters or spaces. Only numbers are accepted.")
    if len(clean_phone) != 10:
        raise ValueError(f"Phone number must contain exactly 10 digits (got {len(clean_phone)} digits).")
    return clean_phone


def validate_email(email: str, required: bool = False) -> str:
    """Validate email address. Email is optional unless required=True.
    
    If provided, it must not start with a capital letter, underscore, or special character,
    and must follow valid email format constraints.
    """
    clean_email = email.strip()
    if not clean_email:
        if required:
            raise ValueError("Email address cannot be empty. Please enter a valid email.")
        return ""
    if clean_email[0].isupper():
        raise ValueError("Email address cannot start with a capital letter. Please enter the email again.")
    if clean_email.startswith("_"):
        raise ValueError("Email address cannot start with an underscore ('_'). Please enter the email again.")
    if not clean_email[0].islower():
        raise ValueError("Email address must start with a lowercase letter. Please enter the email again.")
    if any(c.isspace() for c in clean_email):
        raise ValueError("Email address cannot contain spaces. Please enter the email again.")
    if ".." in clean_email:
        raise ValueError("Email address cannot contain consecutive dots. Please enter the email again.")
    if not EMAIL_REGEX.match(clean_email):
        raise ValueError("Invalid email address format (e.g. name@example.com).")
    return clean_email


def normalize_group(group: str | None) -> str:
    """Ensure the group is one of the default groups, defaulting to 'Other'."""
    if not group or not str(group).strip():
        return "Other"
    clean = str(group).strip().casefold()
    for valid_group in DEFAULT_GROUPS:
        if valid_group.casefold() == clean:
            return valid_group
    return "Other"


class ContactBook:
    """Manage contacts, groups, favorites, and persist them sorted alphabetically."""

    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self.data_file = Path(data_file)
        self.contacts: list[dict[str, Any]] = []
        self.load()

    def sort_contacts(self) -> None:
        """Keep contacts arranged alphabetically by name (case-insensitive)."""
        self.contacts.sort(key=lambda item: item["name"].casefold())

    def load(self) -> None:
        """Load contacts, treating a missing file as an empty book."""
        if not self.data_file.exists():
            self.contacts = []
            return

        try:
            with self.data_file.open("r", encoding="utf-8") as file:
                stored_contacts = json.load(file)
            if not isinstance(stored_contacts, list):
                raise ValueError("Contact data must be a JSON list")
            self.contacts = [self._normalise_contact(contact) for contact in stored_contacts]
            self.sort_contacts()
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
            raise RuntimeError(f"Could not load contacts: {error}") from error

    def save(self) -> None:
        """Write the sorted contacts to disk."""
        try:
            self.sort_contacts()
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            with self.data_file.open("w", encoding="utf-8") as file:
                json.dump(self.contacts, file, indent=2)
        except OSError as error:
            raise RuntimeError(f"Could not save contacts: {error}") from error

    def add(
        self,
        name: str,
        phone: str,
        email: str,
        address: str = "",
        group: str = "Other",
        favorite: bool = False,
    ) -> dict[str, Any]:
        """Add a contact with strict validations, group assignment, and favorite status."""
        clean_name = validate_name(name)
        if self._find_by_name(clean_name):
            raise ValueError(f"A contact named '{clean_name}' already exists. Duplicate contacts are not allowed.")

        contact = self._make_contact(clean_name, phone, email, address, group, favorite)
        self.contacts.append(contact)
        self.sort_contacts()
        return contact

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search contacts by query across name, phone, email, address, group."""
        clean_query = query.strip().casefold()
        if not clean_query:
            raise ValueError("Search text cannot be empty")
        results = [
            contact
            for contact in self.contacts
            if any(clean_query in str(value).casefold() for value in contact.values())
        ]
        return sorted(results, key=lambda c: c["name"].casefold())

    def update(
        self,
        name: str,
        phone: str,
        email: str,
        address: str = "",
        group: str = "Other",
        favorite: bool | None = None,
        new_name: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing contact, verifying new name doesn't collide."""
        existing = self._find_by_name(name)
        if existing is None:
            raise ValueError("Contact not found")

        target_name = validate_name(new_name) if (new_name and new_name.strip()) else existing["name"]
        if target_name.casefold() != existing["name"].casefold() and self._find_by_name(target_name):
            raise ValueError(f"A contact named '{target_name}' already exists. Duplicate contacts are not allowed.")

        target_favorite = existing.get("favorite", False) if favorite is None else bool(favorite)
        updated = self._make_contact(target_name, phone, email, address, group, target_favorite)
        existing.update(updated)
        self.sort_contacts()
        return existing

    def toggle_favorite(self, name: str) -> dict[str, Any]:
        """Toggle the favorite status for a contact."""
        contact = self._find_by_name(name)
        if contact is None:
            raise ValueError("Contact not found")
        contact["favorite"] = not contact.get("favorite", False)
        return contact

    def filter_by_group(self, group: str) -> list[dict[str, Any]]:
        """Filter contacts by specific group, sorted alphabetically A-Z."""
        target_group = normalize_group(group).casefold()
        results = [
            c for c in self.contacts
            if normalize_group(c.get("group", "Other")).casefold() == target_group
        ]
        return sorted(results, key=lambda c: c["name"].casefold())

    def get_favorites(self) -> list[dict[str, Any]]:
        """Get all favorite contacts, sorted alphabetically A-Z."""
        results = [c for c in self.contacts if c.get("favorite", False) is True]
        return sorted(results, key=lambda c: c["name"].casefold())

    def delete(self, name: str) -> dict[str, Any]:
        """Delete a contact by name."""
        contact = self._find_by_name(name)
        if contact is None:
            raise ValueError("Contact not found")
        self.contacts.remove(contact)
        return contact

    def _find_by_name(self, name: str) -> dict[str, Any] | None:
        """Find contact by name (case-insensitive)."""
        name_key = name.strip().casefold()
        return next(
            (contact for contact in self.contacts if contact["name"].casefold() == name_key),
            None,
        )

    @staticmethod
    def _make_contact(
        name: str,
        phone: str,
        email: str,
        address: str = "",
        group: str = "Other",
        favorite: bool = False,
    ) -> dict[str, Any]:
        """Validate all fields and construct contact dictionary."""
        return {
            "name": validate_name(name),
            "phone": validate_phone(phone),
            "email": validate_email(email),
            "address": address.strip(),
            "group": normalize_group(group),
            "favorite": bool(favorite),
        }

    @staticmethod
    def _normalise_contact(contact: Any) -> dict[str, Any]:
        if not isinstance(contact, dict):
            raise ValueError("Each contact must be an object")
        raw_email = str(contact.get("email", "")).strip()
        if raw_email and raw_email[0].isupper():
            raw_email = raw_email[0].lower() + raw_email[1:]
        return ContactBook._make_contact(
            str(contact.get("name", "")),
            str(contact.get("phone", "")),
            raw_email,
            str(contact.get("address", "")),
            str(contact.get("group", "Other")),
            bool(contact.get("favorite", False)),
        )


def prompt_valid_name(book: ContactBook, current_name: str | None = None) -> str:
    """Prompt user for a contact name with duplicate checking loop."""
    prompt_label = f"Name [{current_name}]: " if current_name else "Name: "
    while True:
        raw = input(prompt_label).strip()
        if not raw and current_name:
            return current_name
        try:
            name = validate_name(raw)
            existing = book._find_by_name(name)
            if existing and (current_name is None or existing["name"].casefold() != current_name.casefold()):
                print(f"Error: A contact named '{name}' already exists. Duplicate contacts are not allowed.")
                print("Please enter a different contact name.")
                continue
            return name
        except ValueError as err:
            print(f"Error: {err}")


def prompt_valid_phone(current_phone: str = "") -> str:
    """Prompt user for a valid 10-digit phone number with retry loop."""
    prompt_label = f"Phone (10 digits) [{current_phone}]: " if current_phone else "Phone (10 digits): "
    while True:
        raw = input(prompt_label).strip()
        if not raw and current_phone:
            return current_phone
        try:
            return validate_phone(raw)
        except ValueError as err:
            print(f"Error: {err}")
            print("Please enter the phone number again.")


def prompt_valid_email(current_email: str = "") -> str:
    """Prompt user for a valid email address with retry loop (optional)."""
    prompt_label = f"Email [{current_email}]: " if current_email else "Email (optional): "
    while True:
        raw = input(prompt_label).strip()
        if not raw:
            return current_email if current_email else ""
        try:
            return validate_email(raw)
        except ValueError as err:
            print(f"Error: {err}")
            print("Please enter the email again.")


def prompt_group(current_group: str = "Other") -> str:
    """Prompt user to select a group from the default list."""
    print("Select Group:")
    for idx, grp in enumerate(DEFAULT_GROUPS, start=1):
        indicator = " *" if grp.casefold() == current_group.casefold() else ""
        print(f"{idx}. {grp}{indicator}")

    while True:
        choice = input(f"Enter choice [1-{len(DEFAULT_GROUPS)}] (default: {current_group}): ").strip()
        if not choice:
            return current_group
        if choice.isdigit() and 1 <= int(choice) <= len(DEFAULT_GROUPS):
            return DEFAULT_GROUPS[int(choice) - 1]
        for grp in DEFAULT_GROUPS:
            if grp.casefold() == choice.casefold():
                return grp
        print(f"Please enter a valid choice between 1 and {len(DEFAULT_GROUPS)}.")


def prompt_favorite(current_favorite: bool = False) -> bool:
    """Prompt user to set favorite status (y/n)."""
    default_str = "y" if current_favorite else "n"
    star_icon = "★" if current_favorite else "☆"
    raw = input(f"Mark as favorite {star_icon} (y/n) [{default_str}]: ").strip().lower()
    if not raw:
        return current_favorite
    return raw in ("y", "yes", "true", "1")


def prompt_contact_details(book: ContactBook, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collect contact fields ensuring all validation rules are met without crashing."""
    existing = existing or {}
    name = prompt_valid_name(book, existing.get("name"))
    phone = prompt_valid_phone(existing.get("phone", ""))
    email = prompt_valid_email(existing.get("email", ""))
    address = input(f"Address [{existing.get('address', '')}]: ").strip() or existing.get("address", "")
    group = prompt_group(existing.get("group", "Other"))
    favorite = prompt_favorite(existing.get("favorite", False))

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "group": group,
        "favorite": favorite,
    }


def display_contact_card(contact: dict[str, Any]) -> None:
    """Display all details of a selected contact."""
    star = "★ Yes" if contact.get("favorite") else "☆ No"
    print("\n" + "=" * 40)
    print(f"CONTACT DETAILS: {contact['name'].upper()}")
    print("=" * 40)
    print(f"  Name:     {contact['name']}")
    print(f"  Phone:    {contact['phone']}")
    print(f"  Email:    {contact['email']}")
    print(f"  Address:  {contact['address'] if contact['address'] else '(Not provided)'}")
    print(f"  Group:    {contact.get('group', 'Other')}")
    print(f"  Favorite: {star}")
    print("=" * 40)


def display_alphabetical_contacts(contacts: list[dict[str, Any]], title: str = "Mobile Contacts (Alphabetical Order A–Z)") -> None:
    """Display contacts in mobile-contacts alphabetical order (A-Z) with section grouping."""
    if not contacts:
        print("\nNo contacts found.")
        return

    # Always sort all contacts alphabetically by name (A-Z, case-insensitive) before displaying
    sorted_contacts = sorted(contacts, key=lambda item: item["name"].casefold())

    print(f"\n--- {title} ---")
    current_letter = ""
    for idx, contact in enumerate(sorted_contacts, start=1):
        first_letter = contact["name"][0].upper() if contact["name"] else "#"
        if first_letter != current_letter:
            current_letter = first_letter
            print(f"\n[{current_letter}]")
        star = "★" if contact.get("favorite") else "☆"
        group_badge = f"[{contact.get('group', 'Other')}]"
        print(f"  {idx}. {contact['name']}  ({contact['phone']}) {group_badge} {star}")
    print("------------------------------------------------")


def run() -> None:
    """Run the interactive command-line contact book."""
    try:
        book = ContactBook()
    except RuntimeError as error:
        print(f"Error: {error}")
        return

    while True:
        print("\n=== Contact Book ===")
        print("1. Add contact")
        print("2. Search contacts")
        print("3. View all contacts (Alphabetical & Select Contact)")
        print("4. View contacts by group")
        print("5. View favorite contacts (★)")
        print("6. Update contact")
        print("7. Toggle favorite status (☆ / ★)")
        print("8. Delete contact")
        print("9. Exit")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                print("\n--- Add New Contact ---")
                contact_data = prompt_contact_details(book)
                book.add(**contact_data)
                book.save()
                print(f"\nSuccess: Contact '{contact_data['name']}' added.")
                print("\nAll Contacts (Alphabetical Order):")
                display_alphabetical_contacts(book.contacts)

            elif choice == "2":
                query = input("Search by name, phone, email, address, or group: ").strip()
                if not query:
                    print("Search text cannot be empty.")
                    continue
                results = book.search(query)
                display_alphabetical_contacts(results, f"Search Results for '{query}'")
                if results:
                    sel = input("\nEnter number to view full details (or press Enter to return): ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(results):
                        display_contact_card(results[int(sel) - 1])

            elif choice == "3":
                display_alphabetical_contacts(book.contacts)
                if book.contacts:
                    sel = input("\nEnter number to view full details (or press Enter to return): ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(book.contacts):
                        display_contact_card(book.contacts[int(sel) - 1])

            elif choice == "4":
                print("\n--- View Contacts by Group ---")
                selected_group = prompt_group()
                group_contacts = book.filter_by_group(selected_group)
                display_alphabetical_contacts(group_contacts, f"Group: {selected_group} (Alphabetical Order A–Z)")
                if group_contacts:
                    sel = input("\nEnter number to view full details (or press Enter to return): ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(group_contacts):
                        display_contact_card(group_contacts[int(sel) - 1])

            elif choice == "5":
                favorites = book.get_favorites()
                display_alphabetical_contacts(favorites, "Favorite Contacts ★ (Alphabetical Order A–Z)")
                if favorites:
                    sel = input("\nEnter number to view full details (or press Enter to return): ").strip()
                    if sel.isdigit() and 1 <= int(sel) <= len(favorites):
                        display_contact_card(favorites[int(sel) - 1])

            elif choice == "6":
                name = input("Enter contact name to update: ").strip()
                existing = book._find_by_name(name)
                if existing is None:
                    print(f"Error: Contact '{name}' not found.")
                    continue
                print(f"\n--- Updating '{existing['name']}' ---")
                updated_data = prompt_contact_details(book, existing)
                book.update(
                    existing["name"],
                    phone=updated_data["phone"],
                    email=updated_data["email"],
                    address=updated_data["address"],
                    group=updated_data["group"],
                    favorite=updated_data["favorite"],
                    new_name=updated_data["name"],
                )
                book.save()
                print("\nSuccess: Contact updated.")
                print("\nAll Contacts (Alphabetical Order):")
                display_alphabetical_contacts(book.contacts)

            elif choice == "7":
                name = input("Enter contact name to toggle favorite (☆ / ★): ").strip()
                toggled = book.toggle_favorite(name)
                book.save()
                star = "★ (Favorite)" if toggled.get("favorite") else "☆ (Not Favorite)"
                print(f"\nSuccess: '{toggled['name']}' is now {star}.")

            elif choice == "8":
                name = input("Enter contact name to delete: ").strip()
                deleted = book.delete(name)
                book.save()
                print(f"\nDeleted contact: {deleted['name']}.")
                print("\nAll Contacts (Alphabetical Order):")
                display_alphabetical_contacts(book.contacts)

            elif choice == "9":
                print("Goodbye.")
                return

            else:
                print("Please choose an option from 1 to 9.")
        except (ValueError, RuntimeError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    run()
