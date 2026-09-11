# Birmingham Smart Public Transport Assistant

Production-oriented FastAPI + browser chatbot for Birmingham
public transport.

## Architecture

Browser
  -> FastAPI
  -> NLP / journey engine
  -> TfWM GTFS-RT
  -> live vehicle/trip information

The ETA ML model is stored under:

models/final_eta_gradient_boosting.pkl

## Environment variables

Set these on the server:

TFWM_APP_ID
TFWM_APP_KEY
REFRESH_SECONDS

Never expose TfWM credentials to the browser.

## Local run

pip install -r requirements.txt

uvicorn app:app --host 0.0.0.0 --port 8000

Open:

http://127.0.0.1:8000

## API

GET /health

POST /chat

Example:

{
    "message": "What is my next bus from Coronation Gardens to Colmore Row?"
}

## Important

The application must not claim a live ETA unless the vehicle,
trip and stop sequence can be verified from the live data.

Scheduled information should be explicitly labelled as scheduled.
