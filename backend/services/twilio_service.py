"""
Twilio Service
Handles phone call infrastructure
"""
import os
from urllib.parse import urlencode
from twilio.rest import Client
from typing import Dict, Optional

class TwilioService:
    """Service for managing Twilio phone calls"""

    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.test_number = os.getenv('TEST_CALL_NUMBER')  # Your cofounder's number

        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Twilio credentials not found in environment variables")

        self.client = Client(self.account_sid, self.auth_token)
        print(f"✅ Twilio service initialized (From: {self.phone_number})")

    def make_call(self, to_number: str, agent_prompt: str, booking_context: Dict, provider_name: Optional[str] = None) -> Dict:
        """
        Initiate a phone call using Twilio.
        When TWILIO_WEBHOOK_BASE_URL is set, uses the voice webhook for multi-turn conversation.
        Otherwise uses inline TwiML (single message then record).
        """
        try:
            # For testing, override with test number
            if os.getenv('USE_TEST_NUMBER', 'true').lower() == 'true':
                original_number = to_number
                to_number = self.test_number
                print(f"📞 TEST MODE: Calling {to_number} instead of {original_number}")

            webhook_base = os.getenv('TWILIO_WEBHOOK_BASE_URL', '').rstrip('/')
            service_type = booking_context.get('service_type', 'appointment')
            timeframe = booking_context.get('timeframe', 'this week')

            if webhook_base:
                # Multi-turn: Twilio will request our webhook and we return Say + Gather + follow-up
                client_name = booking_context.get('client_name', 'Alberto Menendez')
                query = urlencode({
                    'step': '0',
                    'service_type': service_type,
                    'timeframe': timeframe,
                    'provider_name': provider_name or '',
                    'client_name': client_name,
                })
                url = f"{webhook_base}/api/twilio/voice?{query}"
                call = self.client.calls.create(
                    url=url,
                    to=to_number,
                    from_=self.phone_number
                )
                print(f"✅ Call initiated (multi-turn): {call.sid} to {to_number}")
            else:
                # Fallback: multiple messages; use timeframe we already have, say Alberto Menendez
                client_name = booking_context.get('client_name', 'Alberto Menendez')
                st = service_type.replace('_', ' ')
                tf = timeframe.replace('_', ' ')
                twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">
        Hello, this is Call Pilot. I'm calling on behalf of {client_name} to book a {st} appointment. He's looking for something {tf}. Are you the right person to schedule that?
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Matthew">
        Please tell me when you can fit him in when you hear the beep. I'll be listening for up to two minutes.
    </Say>
    <Record maxLength="120" playBeep="true" />
    <Say voice="Polly.Matthew">Thank you. We'll follow up shortly. Goodbye.</Say>
    <Hangup/>
</Response>'''
                call = self.client.calls.create(
                    twiml=twiml,
                    to=to_number,
                    from_=self.phone_number
                )
                print(f"✅ Call initiated: {call.sid} to {to_number}")

            return {
                'call_sid': call.sid,
                'status': call.status,
                'to': to_number,
                'from': self.phone_number,
                'start_time': call.date_created
            }

        except Exception as e:
            print(f"❌ Error making call: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed'
            }

    def get_call_status(self, call_sid: str) -> Dict:
        """Get the status of a call"""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'to': call.to,
                'from_': call.from_
            }
        except Exception as e:
            return {'error': str(e)}

    def get_call_recording(self, call_sid: str) -> Optional[str]:
        """Get the recording URL for a call"""
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            if recordings:
                return recordings[0].uri
            return None
        except Exception as e:
            print(f"❌ Error getting recording: {str(e)}")
            return None


# Singleton instance
_twilio_service = None

def get_twilio_service() -> TwilioService:
    """Get or create the Twilio service singleton"""
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioService()
    return _twilio_service
