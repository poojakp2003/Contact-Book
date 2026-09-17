"""Unit tests for ContactBook validation, sorting, groups, favorites, and persistence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from main import ContactBook, validate_email, validate_phone, validate_name, normalize_group, DEFAULT_GROUPS


class ContactBookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temporary_directory.name) / "contacts.json"
        self.book = ContactBook(self.data_file)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_add_and_reload_contact(self) -> None:
        self.book.add("Ada Lovelace", "9876543210", "ada@example.com", "London", group="Work", favorite=True)
        self.book.save()

        reloaded = ContactBook(self.data_file)
        self.assertEqual(len(reloaded.contacts), 1)
        self.assertEqual(reloaded.contacts[0]["name"], "Ada Lovelace")
        self.assertEqual(reloaded.contacts[0]["phone"], "9876543210")
        self.assertEqual(reloaded.contacts[0]["group"], "Work")
        self.assertTrue(reloaded.contacts[0]["favorite"])

    def test_alphabetical_ordering(self) -> None:
        self.book.add("Zara Phillips", "1112223333", "zara@example.com")
        self.book.add("Alan Turing", "2223334444", "alan@example.com")
        self.book.add("Grace Hopper", "3334445555", "grace@example.com")

        names = [c["name"] for c in self.book.contacts]
        self.assertEqual(names, ["Alan Turing", "Grace Hopper", "Zara Phillips"])

    def test_groups_assignment_and_filtering(self) -> None:
        # Default group should be "Other"
        contact_default = self.book.add("Ben Smith", "1234567890", "ben@example.com")
        self.assertEqual(contact_default["group"], "Other")

        # Specific groups
        self.book.add("Neeraj", "1122334455", "neeraj@gmail.com", group="College")
        self.book.add("Alice Brown", "2233445566", "alice@gmail.com", group="College")
        self.book.add("Charlie", "3344556677", "charlie@gmail.com", group="Family")

        # Filter by College should return Alice Brown, then Neeraj (sorted A-Z)
        college_contacts = self.book.filter_by_group("College")
        self.assertEqual(len(college_contacts), 2)
        self.assertEqual([c["name"] for c in college_contacts], ["Alice Brown", "Neeraj"])

        # Case-insensitive group filter
        college_lower = self.book.filter_by_group("college")
        self.assertEqual(len(college_lower), 2)

        # Update contact group
        self.book.update("Neeraj", "1122334455", "neeraj@gmail.com", group="Work")
        self.assertEqual(len(self.book.filter_by_group("College")), 1)
        self.assertEqual(len(self.book.filter_by_group("Work")), 1)

    def test_favorites_toggle_and_filtering(self) -> None:
        self.book.add("Zara", "1111111111", "zara@example.com", favorite=True)
        self.book.add("Alice", "2222222222", "alice@example.com", favorite=True)
        self.book.add("Bob", "3333333333", "bob@example.com", favorite=False)

        # Filter favorites (must be sorted A-Z: Alice, then Zara)
        favorites = self.book.get_favorites()
        self.assertEqual(len(favorites), 2)
        self.assertEqual([c["name"] for c in favorites], ["Alice", "Zara"])

        # Toggle Bob to favorite
        toggled_bob = self.book.toggle_favorite("Bob")
        self.assertTrue(toggled_bob["favorite"])
        self.assertEqual(len(self.book.get_favorites()), 3)

        # Toggle Bob back to not favorite
        toggled_bob_again = self.book.toggle_favorite("Bob")
        self.assertFalse(toggled_bob_again["favorite"])
        self.assertEqual(len(self.book.get_favorites()), 2)

    def test_duplicate_names_are_rejected_case_insensitively(self) -> None:
        self.book.add("Ada Lovelace", "9876543210", "ada@example.com", "London")
        # Exact duplicate
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.book.add("Ada Lovelace", "1234567890", "other@example.com", "Paris")
        # Case-insensitive duplicate (lowercase)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.book.add("ada lovelace", "1234567890", "other@example.com", "Paris")
        # Case-insensitive duplicate (uppercase)
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.book.add("ADA LOVELACE", "1234567890", "other@example.com", "Paris")

    def test_phone_number_must_be_exactly_10_digits(self) -> None:
        # Valid 10 digits
        self.assertEqual(validate_phone("9876543210"), "9876543210")

        # Less than 10 digits
        with self.assertRaisesRegex(ValueError, "exactly 10 digits"):
            validate_phone("12345")

        # More than 10 digits
        with self.assertRaisesRegex(ValueError, "exactly 10 digits"):
            validate_phone("123456789012")

        # Empty phone
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            validate_phone("")

    def test_phone_number_rejects_letters_and_special_characters(self) -> None:
        # Contains letters
        with self.assertRaisesRegex(ValueError, "cannot contain letters"):
            validate_phone("98765abcde")

        # Contains hyphens
        with self.assertRaisesRegex(ValueError, "cannot contain special characters"):
            validate_phone("987-654-3210")

        # Contains spaces
        with self.assertRaisesRegex(ValueError, "cannot contain special characters"):
            validate_phone("987 654 321")

        # Contains symbols
        with self.assertRaisesRegex(ValueError, "cannot contain special characters"):
            validate_phone("+1987654321")

    def test_invalid_email_is_rejected(self) -> None:
        # Missing @
        with self.assertRaisesRegex(ValueError, "Invalid email"):
            validate_email("adalongexample.com")

        # Missing domain extension
        with self.assertRaisesRegex(ValueError, "Invalid email"):
            validate_email("ada@example")

        # Cannot start with capital letter
        with self.assertRaisesRegex(ValueError, "cannot start with a capital letter"):
            validate_email("Pooja12@gmail.com")

        # Cannot start with underscore
        with self.assertRaisesRegex(ValueError, "cannot start with an underscore"):
            validate_email("_pooja@gmail.com")

        # Empty email is allowed by default (optional)
        self.assertEqual(validate_email(""), "")

        # Empty email with required=True raises error
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            validate_email("", required=True)

    def test_contact_with_optional_empty_email(self) -> None:
        contact = self.book.add("Empty Email Contact", "9876543210", "")
        self.assertEqual(contact["email"], "")

    def test_search_update_and_delete(self) -> None:
        self.book.add("Ada Lovelace", "9876543210", "ada@example.com", "London", group="Work")
        self.assertEqual(len(self.book.search("london")), 1)
        self.assertEqual(len(self.book.search("work")), 1)

        # Update contact
        self.book.update("Ada Lovelace", "1234567890", "ada@example.com", "Paris", group="Family")
        self.assertEqual(self.book.contacts[0]["phone"], "1234567890")
        self.assertEqual(self.book.contacts[0]["address"], "Paris")
        self.assertEqual(self.book.contacts[0]["group"], "Family")

        # Delete contact (case-insensitive)
        self.book.delete("ADA LOVELACE")
        self.assertEqual(self.book.contacts, [])


if __name__ == "__main__":
    unittest.main()
