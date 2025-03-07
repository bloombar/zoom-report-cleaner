"""
Need to refactor code in main.py to match tests.
"""

import pytest
from main import fill_missing_emails

def test_fill_missing_emails_all_missing():
    data = [
        {"name": "Alice", "email": None},
        {"name": "Bob", "email": None},
        {"name": "Charlie", "email": None}
    ]
    result = fill_missing_emails(data)
    for entry in result:
        assert entry["email"] is not None

def test_fill_missing_emails_some_missing():
    data = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": None},
        {"name": "Charlie", "email": "charlie@example.com"}
    ]
    result = fill_missing_emails(data)
    assert result[0]["email"] == "alice@example.com"
    assert result[1]["email"] is not None
    assert result[2]["email"] == "charlie@example.com"

def test_fill_missing_emails_none_missing():
    data = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"}
    ]
    result = fill_missing_emails(data)
    assert result == data

def test_fill_missing_emails_empty_list():
    data = []
    result = fill_missing_emails(data)
    assert result == []

def test_fill_missing_emails_no_email_field():
    data = [
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"}
    ]
    result = fill_missing_emails(data)
    for entry in result:
        assert "email" in entry
        assert entry["email"] is not None