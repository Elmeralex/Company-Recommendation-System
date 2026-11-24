import json
from datetime import datetime, timezone
import hashlib
from typing import Final

from sentence_transformers import SentenceTransformer


MODEL_NAME: Final = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_SIZE: Final = 384
_model = None

def message_validation(body: bytes) -> str:
    """Return a status for one raw message. Rough checks for exploring only."""
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        return {"status": "reject", "reason": "bad-json"} 

    #Is it a JSON object
    if not isinstance(event, dict):
        return {"status": "skip", "reason": "is not JSON object"}

    if not isinstance(event.get("data"), dict):
        return {"status": "reject", "reason": "data-not-an-object"}
    
    #lowercase - standardize format
    event_normalized = standardize_value(event)

    #Without a valid registration number we can't store it anywhere and it should start with SYN
    if event_normalized.get("registrationnumber") is None:
        return {"status": "skip", "reason": "missing-registration-number"}
    elif not isinstance(event_normalized.get("registrationnumber"), str) or not event_normalized.get("registrationnumber").startswith("syn-"):
        return {"status": "reject", "reason": "bad-registration-number"}

    #Standardize the timestamp to UTC timezone, to trace the update
    updated_at = standardize_timezone(event_normalized.get("updatedat"))
    if updated_at is None:
        return {"status": "reject", "reason": "bad-updated-at"}
    event_normalized["updatedat"] = updated_at

    return {"status": "saved", "data": event_normalized}

#Convert a timestamp string to a datetime object in UTC timezone
def standardize_timezone(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except ValueError:
        return None

#Lowercase the keys and strip spaces from string values. Recursively standardize nested dictionaries
def standardize_value(event):
    standardized_event = {}
    for key, value in event.items():
        if key.lower() != "updatedat":
            if isinstance(value, str):
                value = value.strip().lower()
                if value == "":
                    value = None
            elif isinstance(value, dict):
                value = standardize_value(value)
        standardized_event[key.lower()] = value   
    return standardized_event

def get_description_hash(description: str) -> str:
    if description is None:
        return None
    return hashlib.sha256(description.encode("utf-8")).hexdigest()

def get_model() -> SentenceTransformer: #Avoid calling more than once
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def get_embedding(description):
    if not description:
        return None
    vector = get_model().encode(description, normalize_embeddings=True)
    return "[" + ",".join(str(float(x)) for x in vector) + "]"