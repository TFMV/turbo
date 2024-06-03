# Turbo Import: Top Gun Edition 🛫

Welcome to Turbo Import, the ultimate data import module in the Turbo Data Integration Suite. Get ready to fly high with seamless and efficient data transfers, just like Maverick in Top Gun. With Turbo Import, you're in the cockpit, ready to execute high-speed data imports into your PostgreSQL database via GCS.

![Turbo Import](assets/turbo.webp)

## Mission Briefing 📝

### Project Overview

Turbo Import is a FastAPI-based service designed for asynchronous data import from Google Cloud Storage (GCS) to PostgreSQL. It's built to handle large-scale data with ease, ensuring your imports are fast, reliable, and smooth as a jet fighter.

### Key Features ✨

- Asynchronous Data Import: Leveraging asyncpg for non-blocking database operations.
- Google Cloud Storage Integration: Directly read compressed CSV files from GCS.
- High Performance: Optimized for large datasets with configurable chunk sizes.
- Error Handling: Robust logging and error management to ensure mission success.

## Pre-Flight Checklist ✔️

### Environment Setup 🛠

Python 3.8+: Ensure you have Python installed.
PostgreSQL: Setup your PostgreSQL instance and ensure it's accessible.
Google Cloud SDK: Install and authenticate using gcloud.

### Installation

```bash
git clone https://github.com/TFMV/turbo.git
cd turbo-import
pip install -r requirements.txt
```

### Environment Variables

Set up the following environment variables to configure your database connection:

```bash
export DB_USER='your_db_user'
export DB_PASS='your_db_password'
export DB_NAME='your_db_name'
```

## Takeoff Procedure 🚀

FastAPI Launch

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### API Endpoint

/import_async

Method: POST

```json
{
  "table_name": "your_table_name",
  "table_schema": "public",
  "bucket_name": "your_bucket_name",
  "file_path": "your_file_path",
  "instance_connection_name": "your_instance_connection_name",
  "chunk_size": 1000000,
  "skip_header": false
}
```

### Response

```json
{
  "message": "Data import successful",
  "gcs_uri": "your_bucket_name/your_file_path.csv.gz",
  "schema_table": "public.your_table_name",
  "time_taken": "0:01:23.456789"
}
```

## Logging and Monitoring 📊

Turbo Import leverages Google Cloud Logging for detailed mission logs. Ensure your GCP project is configured to capture these logs for real-time monitoring and post-mission analysis.

## Top Gun Tips ✈️

Chunk Size: Adjust the chunk_size based on your data and performance benchmarks.
Error Handling: Enhance the error handling in import_async to cover more edge cases.
Logging: Utilize Google Cloud Logging to monitor performance and debug issues.
