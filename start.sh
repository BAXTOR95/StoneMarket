#!/bin/bash

# Run the database migrations
python create_db.py

# Start the Gunicorn server
exec gunicorn app:app
