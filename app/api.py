import psycopg
from fastapi import FastAPI, HTTPException, Query
from app import service

app = FastAPI()

#Get the company for a given registration number
@app.get("/company/{registration_number}")
async def get_company(registration_number: str):
    company = service.get_company(registration_number)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

#Get similar companies for a given registration number
@app.get("/company/{registration_number}/similar")
async def get_similar_companies(registration_number: str):
    similar_companies = service.get_similar_companies(registration_number)
    if not similar_companies:
        raise HTTPException(status_code=404, detail="No similar companies found")
    return similar_companies
