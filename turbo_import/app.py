from asyncio.unix_events import BaseChildWatcher
import base64
import json
import logging
import os
from datetime import datetime
from typing import Optional
import asyncpg
import asyncio
import psycopg2
import ast
import json
import pyarrow.fs as fs
from fastapi import FastAPI, HTTPException
from google.cloud import logging as cloud_logging
from pydantic import BaseModel, Field
import csv
import itertools

# Configure logging
logging.basicConfig(level=logging.INFO)

class PubSubMessage(BaseModel):
    data: Optional[str]
    messageId: Optional[str]

class PubSubRequest(BaseModel):
    message: PubSubMessage
    subscription: str

app = FastAPI()

client = cloud_logging.Client()
client.setup_logging()

class Event(BaseModel):
    data: str = Field(..., description="The actual data of the event.")

class DataParams(BaseModel):
    table_name: str
    table_schema: Optional[str] = "public"
    bucket_name: str
    file_path: str
    instance_connection_name: str
    chunk_size: Optional[int] = 1000000
    skip_header: Optional[bool] = False

@app.post("/import_async")
async def import_async(data_params: DataParams):
    start_time = datetime.now()

    # Retrieve environment variables
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")

    # Validate environment variables
    if not all([db_user, db_pass, db_name]):
        logging.error(
            f"Missing environment variables - DB_USER: {db_user}, DB_PASS: {db_pass}, DB_NAME: {db_name}"
        )
        raise HTTPException(status_code=500, detail="Missing environment variables")

    # Establish database connection
    socket_dir = "/cloudsql"
    unix_socket = f"{socket_dir}/{data_params.instance_connection_name}"
    conn = None
    try:
        conn = await asyncpg.connect(
            database=db_name,
            user=db_user,
            password=db_pass,
            host=unix_socket,
        )
    except Exception as conn_error:
        logging.error(f"Error connecting to database: {conn_error}")
        raise HTTPException(
            status_code=500, detail=f"Error connecting to database: {conn_error}"
        )

    # Access GCS file
    gcs_filesystem = fs.GcsFileSystem()
    gcs_uri = f"{data_params.bucket_name}/{data_params.file_path}"
    try:
        with gcs_filesystem.open_input_stream(gcs_uri, compression="gzip") as file:
            if gcs_uri.endswith(".csv.gz"):
                try:
                    # Ensure table schema exists
                    await conn.execute(
                        f"SET search_path TO {data_params.table_schema};"
                    )
                    await conn.fetch(
                        f'SELECT * FROM "{data_params.table_schema}"."{data_params.table_name}" LIMIT 0;'
                    )
                except Exception as table_error:
                    logging.error(f"Error accessing table: {table_error}")
                    await conn.close()
                    raise HTTPException(
                        status_code=400,
                        detail="Table not found or schema is invalid",
                    )
                # Copy data from GCS to table in chunks
                async def copy_data(file):
                    # Create a csv.reader object to read data from file
                    reader = csv.reader(file)
                    # Use the connection's copy_records_to_table function to copy data
                    async for chunk in chunks(reader, data_params.chunk_size):
                        await conn.copy_records_to_table(
                            data_params.table_name,
                            records=chunk,
                            schema_name=data_params.table_schema,
                            columns=data_params.columns, # Replace with your columns
                        )
                await copy_data(file)
            else:
                logging.warning(
                    f"Unsupported file type: {gcs_uri}. Only CSV.GZ files are currently supported."
                )
                await conn.close()
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {gcs_uri}. Only CSV.GZ files are currently supported."
                )
    except Exception as e:
        logging.error(f"Error accessing GCS file: {e}")
        await conn.close()
        raise HTTPException(status_code=400, detail=f"Error In Processing: {e}")

    await conn.close()

    time_taken = datetime.now() - start_time
    schema_table = f"{data_params.table_schema}.{data_params.table_name}"

    logging.info(
        f"Data import successful for table: {schema_table}, time taken: {time_taken}"
    )

    return {
        "message": "Data import successful",
        "gcs_uri": gcs_uri,
        "schema_table": schema_table,
        "time_taken": str(time_taken),
    }

async def chunks(iterable, size):
    """Yield successive n-sized chunks from iterable."""
    iterator = iter(iterable)
    while True:
        chunk = list(itertools.islice(iterator, size))
        if not chunk:
            break
        yield chunk