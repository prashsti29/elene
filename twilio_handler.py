from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from state import call_sessions, CallerState
from agent import get_agent_response
import os
import os

router = APIRouter(prefix="/twilio")

@router.post("/voice")
async def incoming_call(request: Request, CallSid: str = Form(...)):
    if CallSid not in call_sessions:
        call_sessions[CallSid] = CallerState()

    opening = "Hello! Thank you for calling. I'm an AI assistant helping with property listings. Could you please tell me your full name?"

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/twilio/respond",
        speech_timeout=5,
        action_on_empty_result=True,
        language="en-IN"
    )
    gather.say(opening, voice="Polly.Aditi", language="en-IN")
    response.append(gather)

    return Response(content=str(response), media_type="application/xml")


@router.post("/respond")
async def handle_response(
    request: Request,
    CallSid: str = Form(...),
    SpeechResult: str = Form(default="")
):
    state = call_sessions.get(CallSid)
    if not state:
        return _end_call("Session expired, please call again.")

    state.conversation_history.append({"role": "user", "content": SpeechResult})

    agent_reply = await get_agent_response(state, SpeechResult)

    state.conversation_history.append({"role": "assistant", "content": agent_reply})

    response = VoiceResponse()

    if state.is_complete() and state.data_saved:
        response.say("Thank you! We have all your details. Goodbye!")
        response.hangup()
    else:
        gather = Gather(
            input="speech",
            action="/twilio/respond",
            speech_timeout=5,
            action_on_empty_result=True,
            language="en-IN"
        )
        gather.say(agent_reply, voice="Polly.Aditi", language="en-IN")
        response.append(gather)

    return Response(content=str(response), media_type="application/xml")


def _end_call(message: str):
    response = VoiceResponse()
    response.say(message)
    response.hangup()
    return Response(content=str(response), media_type="application/xml")