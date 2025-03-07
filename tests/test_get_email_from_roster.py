"""
Need to refactor code in main.py to match tests.
"""

import pytest
from main import get_email_from_roster

def test_get_email_from_roster_valid_user():
    roster = {
        'alice': 'alice@example.com',
        'bob': 'bob@example.com',
        'charlie': 'charlie@example.com'
    }
    assert get_email_from_roster(roster, 'alice') == 'alice@example.com'
    assert get_email_from_roster(roster, 'bob') == 'bob@example.com'
    assert get_email_from_roster(roster, 'charlie') == 'charlie@example.com'

def test_get_email_from_roster_invalid_user():
    roster = {
        'alice': 'alice@example.com',
        'bob': 'bob@example.com',
        'charlie': 'charlie@example.com'
    }
    assert get_email_from_roster(roster, 'dave') is None

def test_get_email_from_roster_empty_roster():
    roster = {}
    assert get_email_from_roster(roster, 'alice') is None

def test_get_email_from_roster_case_sensitivity():
    roster = {
        'alice': 'alice@example.com',
        'bob': 'bob@example.com',
        'charlie': 'charlie@example.com'
    }
    assert get_email_from_roster(roster, 'Alice') is None
    assert get_email_from_roster(roster, 'BOB') is None
    assert get_email_from_roster(roster, 'Charlie') is None

def test_get_email_from_roster_none_user():
    roster = {
        'alice': 'alice@example.com',
        'bob': 'bob@example.com',
        'charlie': 'charlie@example.com'
    }
    assert get_email_from_roster(roster, None) is None