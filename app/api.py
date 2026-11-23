from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from app import service

app = FastAPI()

#Interface 
INDEX_PAGE = Path(__file__).parent / "index.html"

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index():
    return INDEX_PAGE.read_text(encoding="utf-8")

#-----------
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
