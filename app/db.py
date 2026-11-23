import psycopg
from psycopg.rows import dict_row
import os
from typing_extensions import Final
import app.normalization as normalization

DATABASE_URL: Final = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/companies?connect_timeout=5")

#Create table
CREATE_TABLES = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS companies (
    registration_number text PRIMARY KEY,
    company_name        text,                         -- empty only for a struck-off company we never saw
    nature_of_business  text,
    state               text,
    industry            text,
    description_hash    text,                         -- to reuse embeddings for identical descriptions
    embedding           vector({normalization.EMBEDDING_SIZE}), -- empty when there is no description
    updated_at          timestamptz NOT NULL,         -- updatedAt of the newest event we applied
    last_message_id     text
);

CREATE INDEX IF NOT EXISTS companies_description_hash_idx ON companies (description_hash);
"""
#Open connection to the database
def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

#Create tables in the database
def create_tables(conn):
    conn.execute(CREATE_TABLES)
    conn.commit()

# Call by Consumer (Update, Insert, Get: Existing company. find_embeddings)----------

#Insert company data into the database
def insert_company(conn, event, description_hash, embedding, message_id):
    conn.execute(
        """
        INSERT INTO companies (registration_number, company_name, nature_of_business, state, industry,
                               description_hash, embedding, updated_at, last_message_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            event["registrationnumber"],
            event["data"]["companyname"],
            event["data"]["natureofbusiness"],
            event["data"]["state"],
            event["data"]["industry"],
            description_hash,
            embedding,
            event["updatedat"],
            message_id,
        ),
    )
    conn.commit()

#update company data in the database
def update_company(conn, event, description_hash, embedding, message_id):
    conn.execute(
        """
        UPDATE companies
        SET company_name = %s,
            nature_of_business = %s,
            state = %s,
            industry = %s,
            description_hash = %s,
            embedding = %s,
            updated_at = %s,
            last_message_id = %s
        WHERE registration_number = %s
        """,
        (
            event["data"]["companyname"],
            event["data"]["natureofbusiness"],
            event["data"]["state"],
            event["data"]["industry"],
            description_hash,
            embedding,
            event["updatedat"],
            message_id,
            event["registrationnumber"],
        ),
    )
    conn.commit()

# If another company has exactly the same description, reuse its embedding.
def find_embedding_by_hash(conn, description_hash):
    row = conn.execute(
        "SELECT embedding::text AS embedding FROM companies "
        "WHERE description_hash = %s AND embedding IS NOT NULL LIMIT 1",
        (description_hash,),
    ).fetchone()
    if row is None:
        return None
    return row["embedding"]

def get_updated_at(conn, registration_number):
    """Get the updated_at timestamp for a company, or None if we don't have it."""
    row = conn.execute(
        "SELECT updated_at FROM companies WHERE registration_number = %s FOR UPDATE",
        (registration_number,),
    ).fetchone()
    if row is None:
        return None
    return row["updated_at"]

# Use for service ----
def get_company(conn, registration_number):
    row = conn.execute(
        "SELECT * FROM companies WHERE registration_number = %s",
        (registration_number,),
    ).fetchone()
    return row

#Using pgvector to find similar companies based on the embedding of the nature of business
def find_similar(conn, registration_number, limit=4):
    row = conn.execute(
        "SELECT embedding FROM companies WHERE registration_number = %s",
        (registration_number,),
    ).fetchone()
    if row is None or row["embedding"] is None:
        return []

    embedding = row["embedding"]
    rows = conn.execute(
        """
        SELECT registration_number, company_name, nature_of_business, state, industry
        FROM companies
        WHERE embedding IS NOT NULL AND registration_number != %s
        ORDER BY embedding <-> %s
        LIMIT %s
        """,
        (registration_number, embedding, limit),
    ).fetchall()
    return rows