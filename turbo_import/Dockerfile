FROM --platform=linux/amd64 python:3.11-slim

# The environment variable ensures that the python output is set straight
# to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update \
    && apt-get -y install gcc \
    && apt-get clean

# Install psycopg2 dependencies
RUN apt-get install -y postgresql-server-dev-all musl-dev

# Install Python dependencies
COPY requirements.txt $APP_HOME
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . $APP_HOME

# Chown all the files to the app user
RUN chown -R app:app $APP_HOME

# Change to the app user
USER app

# Run the application:
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
