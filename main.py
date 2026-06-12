from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from handlers.twilio_handler import router as twilio_router
from pyngrok import ngrok
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("audio", exist_ok=True)
app.include_router(twilio_router)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

@app.get("/")
def health_check():
    return {"status": "Voice agent running"}

if __name__ == "__main__":
    public_url = ngrok.connect(8000)
    print(f"\n Public URL (paste this in Twilio): {public_url}/twilio/voice\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)