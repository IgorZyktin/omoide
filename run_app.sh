#!/bin/bash
source venv/bin/activate
uvicorn omoide.presentation.app:app --port 8080
