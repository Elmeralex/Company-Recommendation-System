# Art as the module for the service layer of the application, transfer data between the database and interface.

import app.db as db #Import the database module

def get_company(registration_number: str):
    conn = db.connect() #Connect to the database using the database module
    registration_number = registration_number.strip().lower() #Standardize the registration number to lowercase and remove leading/trailing spaces
    company = db.get_company(conn, registration_number) #Get the company from the database using the database module
    conn.close() #Close the connection to the database
    return company

def get_similar_companies(registration_number: str):
    conn = db.connect() #Connect to the database using the database module
    registration_number = registration_number.strip().lower() #Standardize the registration number to lowercase and remove leading/trailing spaces
    similar_companies = db.find_similar(conn, registration_number) #Get the similar companies from the database using the database module
    conn.close() #Close the connection to the database
    return similar_companies