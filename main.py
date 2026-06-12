# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from twilio_handler import router as twilio_router
from pyngrok import ngrok
import uvicorn

app = FastAPI()

# Allow all origins (fine for dev/demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register twilio routes
app.include_router(twilio_router)

@app.get("/")
def health_check():
    return {"status": "Voice agent running"}

if __name__ == "__main__":
    # Expose localhost to internet so Twilio can reach your machine
    public_url = ngrok.connect(8000)
    print(f"\n✅ Public URL (paste this in Twilio): {public_url}/twilio/voice\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)