from ast import Param
from datetime import datetime

from fastapi import FastAPI, Depends, Query, Path, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
from asyncpg.pool import Pool
from Models.BondData import BondData
from Models.StocksData import StockData

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (replace with specific origins if needed)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allow specific HTTP methods
    allow_headers=["*"],  # Allow all headers (replace with specific headers if needed)
)

# Database connection pool
database_pool: Pool = None

# Database configuration
DATABASE_URL = "postgresql://shpendi:pwd@localhost:5433/portfolio"


# Function to initialize database connection pool
async def connect_to_database():
    global database_pool
    database_pool = await asyncpg.create_pool(DATABASE_URL)


# Function to close database connection pool
async def close_database_connection():
    await database_pool.close()


# Dependency to get a database connection from the pool
async def get_database_connection():
    try:
        async with database_pool.acquire() as connection:
            yield connection
    except Exception as ex:
        # If database pool is not initialized, attempt to connect to the database
        await connect_to_database()
        async with database_pool.acquire() as connection:
            yield connection


@app.get("/")
async def root():
    return {"message": "Hello World"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom Swagger UI",
        version="2.5.0",
        description="This is a custom FastAPI schema",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/stocks")
async def say_hello(database: asyncpg.Connection = Depends(get_database_connection)):
    query = "SELECT * from holdings_stocks"
    result = await database.fetch(query)
    return result

@app.get("/stocks/{id}")
async def say_hello(id: str, database: asyncpg.Connection = Depends(get_database_connection)):
    id = int(id)
    query = "SELECT * from holdings_stocks WHERE user_id = $1"
    result = await database.fetch(query, id)
    return result


@app.get("/user/exist/{username}")
async def check_user_exists(database: asyncpg.Connection = Depends(get_database_connection),
                            username: str = Path(..., min_length=1)):
    query = "SELECT EXISTS (SELECT 1 FROM users WHERE username = $1)"
    exists = await database.fetchval(query, username)
    return {"exists": exists}


@app.post('/stocks')
async def insert_stocks(data: StockData, database: asyncpg.Connection = Depends(get_database_connection)):
    date_object = datetime.strptime(data.purchaseDate, '%Y-%m-%d')
    query = '''
           INSERT INTO holdings_stocks (stock_symbol, user_id, shares, purchase_price, purchase_date)
           VALUES ($1, $2, $3, $4, $5)
           RETURNING holding_id
       '''
    record = await database.fetchrow(query, data.name, data.user_id, data.amount, data.purchasePrice, date_object)
    if record:
        return {"message": "Stock data saved", "stock_id": record['holding_id']}
    else:
        raise HTTPException(status_code=500, detail="Failed to save stock data")

@app.post('/bonds')
async def insert_bonds(data: BondData, database: asyncpg.Connection = Depends(get_database_connection)):
    date_object = datetime.strptime(data.purchaseDate, '%Y-%m-%d')
    query = '''
              INSERT INTO holdings_bonds (bond_name, user_id, face_value, purchase_price, purchase_date)
              VALUES ($1, $2, $3, $4, $5)
              RETURNING holding_id
          '''
    record = await database.fetchrow(query, data.name, data.user_id, data.amount, data.purchasePrice, date_object)
    if record:
        return {"message": "Bond data saved", "bond_id": record['holding_id']}
    else:
        raise HTTPException(status_code=500, detail="Failed to save bond data")

@app.on_event("startup")
async def startup_event():
    await connect_to_database()


@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "db_pool"):
        await app.state.db_pool.close()

