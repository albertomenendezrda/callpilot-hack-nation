"""
ElevenLabs Voice AI Service
Handles voice agent creation and call management using ElevenLabs Conversational AI.
Uses agent prompts from agent_prompts.py (get_first_message, get_agent_prompt) so the
conversation continues after the first message via prompt override (no first_message override).
"""
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import requests
import asyncio
import time
from elevenlabs import ElevenLabs

# Use our booking agent prompts (first message + full system prompt)
try:
    from agent_prompts import get_first_message, get_agent_prompt
except ImportError:
    import sys
    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend not in sys.path:
        sys.path.insert(0, _backend)
    from agent_prompts import get_first_message, get_agent_prompt


class ElevenLabsService:
    """Service for managing ElevenLabs voice AI agents"""

    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

        self.client = ElevenLabs(api_key=self.api_key)
        self.agent_id = os.getenv('ELEVENLABS_AGENT_ID', '').strip()
        self.agent_phone_number_id = os.getenv('ELEVENLABS_AGENT_PHONE_NUMBER_ID', '').strip()
        print(f"✅ ElevenLabs service initialized (agent_id={'set' if self.agent_id else 'not set'})")

    def create_booking_agent(self, provider_info: Dict, booking_context: Dict) -> str:
        """
        Create a voice agent configuration for booking (in-memory id for simulated path).
        When using real ElevenLabs outbound calls, we use ELEVENLABS_AGENT_ID + overrides.
        """
        service_type = booking_context.get('service_type', 'appointment')
        timeframe = booking_context.get('timeframe', 'this week')

        system_prompt = get_agent_prompt(
            service_type=service_type,
            client_name="CallPilot",
            timeframe=timeframe,
        )

        agent_id = f"agent_{provider_info['name'].replace(' ', '_')}_{int(time.time())}"
        print(f"🤖 Created agent config {agent_id} for {provider_info['name']}")

        return agent_id

    def make_elevenlabs_outbound_call(
        self,
        to_number: str,
        provider_name: str,
        booking_context: Dict,
    ) -> Dict:
        """
        Place an outbound call via ElevenLabs Conversational AI + Twilio.
        Uses get_first_message() and get_agent_prompt() as overrides so the agent
        says the right opening line and keeps the conversation going (multi-turn).

        Requires ELEVENLABS_AGENT_ID and ELEVENLABS_AGENT_PHONE_NUMBER_ID to be set.
        In dashboard, enable "System prompt" override for the agent (opening line is included in the prompt).
        """
        if not self.agent_id or not self.agent_phone_number_id:
            return {
                'status': 'failed',
                'error': 'ELEVENLABS_AGENT_ID and ELEVENLABS_AGENT_PHONE_NUMBER_ID must be set for ElevenLabs outbound calls',
            }

        service_type = booking_context.get('service_type', 'appointment')
        timeframe = booking_context.get('timeframe', 'this week')
        location = booking_context.get('location', '')
        client_name = booking_context.get('client_name', 'Alberto Menendez')
        preferred_slots = (booking_context.get('preferred_slots') or '').strip()
        party_size = (booking_context.get('party_size') or '').strip()
        business_name = (booking_context.get('business_name') or '').strip() or provider_name
        business_type = (booking_context.get('business_type') or '').strip() or service_type

        system_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        full_prompt = get_agent_prompt(
            service_type=service_type,
            client_name=client_name,
            timeframe=timeframe,
            system_time_utc=system_time_utc,
            system_called_number=to_number,
            preferred_slots=preferred_slots,
            party_size=party_size,
            business_name=business_name,
            business_type=business_type,
        )

        first_message = get_first_message(
            service_type=service_type,
            timeframe=timeframe,
            client_name=client_name,
            preferred_slots=preferred_slots,
            party_size=party_size,
            business_name=business_name,
            business_type=business_type,
        )
        # Prepend first-message instruction to prompt (avoids needing "First message" override enabled on agent)
        prompt_with_opening = f'''# First message (say this when the call is answered)
When the recipient answers, say exactly this first: "{first_message}"
Then continue the conversation according to the rules below.

---
{full_prompt}'''

        # Dynamic variables: the agent prompt uses {{client_name}}, {{system_time_utc}}, {{system_called_number}}, {{appointment_timeframe}}, {{preferred_slots}}, {{party_size}}, {{business_name}}, {{business_type}}.
        slots_value = preferred_slots or timeframe or "the client's preferred timeframe"
        dynamic_variables = {
            "client_name": client_name,
            "system_time_utc": system_time_utc,
            "system_called_number": to_number,
            "appointment_timeframe": timeframe or "the client's preferred timeframe",
            "preferred_slots": slots_value,
            "party_size": party_size or "",
            "business_name": business_name or "",
            "business_type": business_type or "",
        }
        # Use a direct HTTP request with a body that contains ONLY the prompt override (no first_message key).
        url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
        payload = {
            "agent_id": self.agent_id,
            "agent_phone_number_id": self.agent_phone_number_id,
            "to_number": to_number,
            "conversation_initiation_client_data": {
                "conversation_config_override": {
                    "agent": {
                        "prompt": {"prompt": prompt_with_opening},
                    }
                },
                "dynamic_variables": dynamic_variables,
            },
        }
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if not resp.ok:
                err = resp.text
                try:
                    body = resp.json()
                    msg = body.get("message") or body.get("detail") or err
                    err = msg if isinstance(msg, str) else str(body)
                except Exception:
                    pass
                if resp.status_code == 404 and "document_not_found" in str(err).lower():
                    print("❌ ElevenLabs outbound call failed: Phone number or agent not found. Check ELEVENLABS_AGENT_PHONE_NUMBER_ID and ELEVENLABS_AGENT_ID in .env — get the current IDs from the ElevenLabs dashboard (Phone Numbers and Agents).")
                else:
                    print(f"❌ ElevenLabs outbound call failed: {resp.status_code} {err}")
                return {'status': 'failed', 'error': err if isinstance(err, str) else str(err)}
            data = resp.json()
            call_sid = data.get("call_sid") or data.get("callSid")
            conversation_id = data.get("conversation_id")
            print(f"✅ ElevenLabs outbound call started to {to_number} (conversation continues until hangup)")
            return {
                'call_sid': call_sid,
                'conversation_id': conversation_id,
                'status': 'initiated',
                'to': to_number,
                'from': 'elevenlabs',
            }
        except Exception as e:
            print(f"❌ ElevenLabs outbound call failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    async def initiate_call(self, agent_id: str, phone_number: str, context: Dict) -> Dict:
        """
        Initiate a call using the voice agent

        Note: This integrates with ElevenLabs Conversational AI and Twilio.
        The actual implementation requires WebSocket connections for real-time audio streaming.

        Args:
            agent_id: ID of the voice agent
            phone_number: Provider's phone number
            context: Contextual information for the call

        Returns:
            call_info: Information about the initiated call
        """
        try:
            print(f"📞 Initiating call to {phone_number} with agent {agent_id}")

            # Simulate call duration (in production this would be a real call)
            await asyncio.sleep(2)  # Simulated call time

            # In production, this would:
            # 1. Use Twilio to call the number
            # 2. Connect Twilio's audio stream to ElevenLabs Conversational AI
            # 3. Let the agent converse naturally with tool calling enabled
            # 4. Extract booking information from the conversation

            call_result = {
                'call_id': f"call_{int(time.time())}",
                'agent_id': agent_id,
                'phone_number': phone_number,
                'status': 'completed',
                'duration': 45,  # seconds
                'result': self._simulate_call_result(context)
            }

            print(f"✅ Call completed: {call_result['call_id']}")
            return call_result

        except Exception as e:
            print(f"❌ Error initiating call: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _simulate_call_result(self, context: Dict) -> Dict:
        """
        Simulate what an actual ElevenLabs agent would return after a conversation
        In production, this would be extracted from the conversation transcript and tool calls
        """
        import random
        from datetime import datetime, timedelta

        # Simulate that 80% of calls successfully get availability
        has_availability = random.random() < 0.8

        if has_availability:
            days_out = random.randint(1, 14)
            available_date = (datetime.now() + timedelta(days=days_out)).strftime('%A, %B %d')
            available_time = random.choice(['9:00 AM', '10:30 AM', '2:00 PM', '3:30 PM', '4:00 PM'])

            return {
                'success': True,
                'has_availability': True,
                'earliest_slot': {
                    'date': available_date,
                    'time': available_time
                },
                'conversation_summary': f'Receptionist confirmed availability on {available_date} at {available_time}',
                'booking_confirmed': False  # Would confirm in second call
            }
        else:
            return {
                'success': True,
                'has_availability': False,
                'conversation_summary': 'Receptionist stated no availability for the requested timeframe',
                'next_available': 'in 3 weeks'
            }

    async def parallel_calls(self, providers: List[Dict], context: Dict) -> List[Dict]:
        """
        Initiate parallel calls to multiple providers (Swarm Mode)
        This is the KEY CallPilot feature - calling 15 providers simultaneously

        Args:
            providers: List of provider information dictionaries
            context: Booking context (service type, timeframe, etc.)

        Returns:
            results: List of call results from all providers
        """
        print(f"🚀 SWARM MODE: Calling {len(providers)} providers in parallel...")

        # Create tasks for all calls
        tasks = []
        for provider in providers:
            # Create agent for this provider
            agent_id = self.create_booking_agent(provider, context)

            # Create async task for the call
            task = self.initiate_call(agent_id, provider['phone'], context)
            tasks.append(task)

        # Execute all calls in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and format results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Call to {providers[i]['name']} failed: {str(result)}")
            else:
                successful_results.append({
                    'provider': providers[i],
                    'call_result': result
                })

        print(f"✅ Swarm complete: {len(successful_results)}/{len(providers)} calls successful")
        return successful_results


# Singleton instance
_elevenlabs_service = None

def get_elevenlabs_service() -> ElevenLabsService:
    """Get or create the ElevenLabs service singleton"""
    global _elevenlabs_service
    if _elevenlabs_service is None:
        _elevenlabs_service = ElevenLabsService()
    return _elevenlabs_service
