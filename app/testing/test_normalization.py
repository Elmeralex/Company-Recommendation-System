import json
import pytest
from datetime import datetime, timezone

from app.normalization import message_validation, standardize_timezone, get_description_hash

message = {
    "type": "company-upserted",
    "registrationNumber": "SYN-001777",
    "updatedAt": "2026-08-14T09:00:00+08:00",
    "data": {
            "companyName": "Global Maju Packaging Sdn. Bhd.",
            "natureOfBusiness": "Production of rubber gloves for export",
            "state": "Negeri Sembilan",
            "industry": "Manufacturing",
        }
}

def test_message_validation():
    # Convert the message to bytes
    test_message_bytes = json.dumps(message).encode('utf-8')
    assert message_validation(test_message_bytes)["status"] == "saved"

    # Test missing registrationNumber
    invalid_message = message.copy()
    del invalid_message["registrationNumber"]
    test_invalid_message_bytes = json.dumps(invalid_message).encode('utf-8')
    assert message_validation(test_invalid_message_bytes)["status"] == "skip"

    # Test missing updatedAt
    invalid_message = message.copy()
    del invalid_message["updatedAt"]
    test_invalid_message_bytes = json.dumps(invalid_message).encode('utf-8')
    assert message_validation(test_invalid_message_bytes)["status"] == "reject"

    # Test missing data
    invalid_message = message.copy()
    del invalid_message["data"]
    test_invalid_message_bytes = json.dumps(invalid_message).encode('utf-8')
    assert message_validation(test_invalid_message_bytes)["status"] == "reject"

def test_standardize_timezone():
    # Test with timezone info
    dt_str = "2026-08-14T09:00:00+08:00"
    dt_utc = standardize_timezone(dt_str)
    assert dt_utc.isoformat() == "2026-08-14T01:00:00+00:00"

    # Test without timezone info
    dt_str = "2026-08-14T09:00:00"
    dt_utc = standardize_timezone(dt_str)
    assert dt_utc.isoformat() == "2026-08-14T09:00:00+00:00"

    # Test invalid format
    dt_str = "invalid-datetime"
    assert standardize_timezone(dt_str) is None

def test_get_description_hash():
    description = "This is a test description."
    expected_hash = "20685ff88c0e3e51b1251596495dfdf60feb44ab9aef30abcd49c063fc8123b1"
    assert get_description_hash(description) == expected_hash

    # Test with None
    assert get_description_hash(None) is None