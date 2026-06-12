# twilio_handler.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from state import call_sessions, CallerState
from agent import get_agent_response
from tts import text_to_speech
import os

router = APIRouter(prefix="/twilio")

@router.post("/voice")
async def incoming_call(request: Request, CallSid: str = Form(...)):
    """
    Twilio hits this endpoint the moment someone calls your number.
    CallSid is Twilio's unique ID for this call — we use it to track state.
    """
    
    # Create a fresh state for this new call
    if CallSid not in call_sessions:
        call_sessions[CallSid] = CallerState()

    # Build opening message
    opening = "Hello! Thank you for calling. I'm an AI assistant helping with property listings. Could you please tell me your full name?"

    # Convert text to audio file
    audio_path = text_to_speech(opening, CallSid)

    # TwiML = XML instructions that tell Twilio what to do
    response = VoiceResponse()
    
    # Play our audio greeting
    response.play(f"/audio/{CallSid}_response.mp3")
    
    # Gather = tell Twilio to record what the caller says next
    # Then send that recording to /twilio/respond
    gather = Gather(
        input="speech",           # we want speech not keypad
        action="/twilio/respond", # where to send the caller's response
        speech_timeout="auto",    # auto-detect when caller stops speaking
        language="en-IN"          # Indian English
    )
    response.append(gather)

    return Response(content=str(response), media_type="application/xml")


@router.post("/respond")
async def handle_response(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(default="")  # Twilio transcribes basic speech for us
):
    """
    Every time the caller finishes speaking, Twilio sends the transcript here.
    This is the main conversation loop.
    """

    state = call_sessions.get(CallSid)
    if not state:
        return _end_call("Session expired, please call again.")

    # Add caller's message to conversation history
    state.conversation_history.append({
        "role": "user",
        "content": SpeechResult
    })

    # Send to agent brain — it figures out what to extract + what to ask next
    agent_reply = await get_agent_response(state, SpeechResult)

    # Add agent reply to history
    state.conversation_history.append({
        "role": "assistant", 
        "content": agent_reply
    })

    # Convert agent reply to audio
    text_to_speech(agent_reply, CallSid)

    # Build TwiML response
    response = VoiceResponse()
    response.play(f"/audio/{CallSid}_response.mp3")

    # If all data collected, end call
    if state.is_complete() and state.data_saved:
        response.say("Thank you! We have all your details. Goodbye!")
        response.hangup()
    else:
        # Otherwise keep listening
        gather = Gather(
            input="speech",
            action="/twilio/respond",
            speech_timeout="auto",
            language="en-IN"
        )
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")


def _end_call(message: str):
    """Helper to cleanly end a call with a message"""
    response = VoiceResponse()
    response.say(message)
    response.hangup()
    return Response(content=str(response), media_type="application/xml")