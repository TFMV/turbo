from asyncio.unix_events import BaseChildWatcher
import base64
import json
import logging
import os
import re
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

    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")

    logging.info(
        f"Environment variables - DB_USER: {db_user}, DB_PASS: {db_pass}, DB_NAME: {db_name}"
    )

    socket_dir = "/cloudsql"
    unix_socket = f"{socket_dir}/{data_params.instance_connection_name}"

    conn = await asyncpg.connect(
        database=db_name,
        user=db_user,
        password=db_pass,
        host=unix_socket,
    )

    gcs_filesystem = fs.GcsFileSystem()
    gcs_uri = f"{data_params.bucket_name}/{data_params.file_path}"
    try:
        with gcs_filesystem.open_input_stream(gcs_uri, compression="gzip") as file:
            if gcs_uri.endswith(".csv.gz"):
                try:
                    await conn.execute(
                        f"SET search_path TO {data_params.table_schema};"
                    )
                    try:
                        await conn.fetch(
                            f'SELECT * FROM "{data_params.table_schema}"."{data_params.table_name}" LIMIT 0;'
                        )
                    except Exception as table_error:
                        logging.error(f"Error accessing table: {table_error}")
                        raise HTTPException(
                            status_code=400,
                            detail="Table not found or schema is invalid",
                        )
                    await conn.copy_records_to_table(
                        data_params.table_name,
                        records=[row for row in csv.reader(file)],
                        schema_name=data_params.table_schema,
                        columns=data_params.columns,  # Replace with your columns
                    )
                except Exception as cursor_error:
                    logging.error(f"Error executing copy command: {cursor_error}")
                    raise
    except Exception as e:
        logging.error(f"Error accessing GCS file: {e}")
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
