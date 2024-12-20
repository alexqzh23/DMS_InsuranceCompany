import urllib.parse
import os

DRIVER = '{ODBC Driver 18 for SQL Server}'
SERVER = 'dmsprojectserver.database.windows.net,1433'
DATABASE = 'InsuranceCompany'
UID = 'dmsadmin'
PWD = 'alexqizq2201!'
ENCRYPT = 'yes'
TRUST_SERVER_CERTIFICATE = 'no'
TIMEOUT = 30

params = urllib.parse.quote_plus(
    f"DRIVER={DRIVER};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"UID={UID};"
    f"PWD={PWD};"
    f"Encrypt={ENCRYPT};"
    f"TrustServerCertificate={TRUST_SERVER_CERTIFICATE};"
    f"Connection Timeout={TIMEOUT};"
)

SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.urandom(24)
