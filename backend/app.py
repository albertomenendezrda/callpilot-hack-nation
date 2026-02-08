from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid
import time
import threading
from datetime import datetime, timedelta
import random
import asyncio

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Import services for real calling
from services.google_service import get_google_service
from services.elevenlabs_service import get_elevenlabs_service
from services.twilio_service import get_twilio_service

# Import database
import database as db

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize database on startup
db.init_db()

def get_mock_cambridge_providers(service_type):
    """Get mock providers for Cambridge, MA to avoid Google API costs"""

    # Realistic Cambridge, MA addresses
    cambridge_addresses = [
        "1 Massachusetts Ave, Cambridge, MA 02139",
        "730 Massachusetts Ave, Cambridge, MA 02139",
        "874 Massachusetts Ave, Cambridge, MA 02139",
        "2067 Massachusetts Ave, Cambridge, MA 02140",
        "50 JFK St, Cambridge, MA 02138",
        "1815 Massachusetts Ave, Cambridge, MA 02140",
        "625 Mt Auburn St, Cambridge, MA 02138",
        "907 Main St, Cambridge, MA 02139",
        "145 Huron Ave, Cambridge, MA 02138",
        "520 Concord Ave, Cambridge, MA 02138",
        "350 Massachusetts Ave, Cambridge, MA 02139",
        "1105 Massachusetts Ave, Cambridge, MA 02138",
        "923 Massachusetts Ave, Cambridge, MA 02139",
        "2000 Massachusetts Ave, Cambridge, MA 02140",
        "1682 Massachusetts Ave, Cambridge, MA 02138"
    ]

    provider_data = {
        'dentist': [
            'Cambridge Dental Associates', 'Harvard Square Dental', 'Central Square Smiles',
            'Porter Dental Group', 'Kendall Dentistry', 'Fresh Pond Dental Care',
            'MIT Dental Clinic', 'Inman Square Dental', 'Huron Village Dentistry',
            'North Cambridge Dental', 'East Cambridge Dental', 'Riverside Dental Care',
            'Cambridge Family Dentistry', 'Harvard Dental Center', 'Porter Square Dental'
        ],
        'doctor': [
            'Cambridge Health Alliance', 'Harvard Medical Group', 'Mount Auburn Medical',
            'Central Square Family Practice', 'Porter Primary Care', 'Kendall Medical Center',
            'Fresh Pond Healthcare', 'MIT Medical', 'Inman Square Clinic',
            'North Cambridge Medical', 'East Cambridge Health', 'Riverside Primary Care',
            'Cambridge Family Medicine', 'Harvard Community Health', 'Porter Square Medical'
        ],
        'hair_salon': [
            'Cambridge Hair Studio', 'Harvard Square Salon', 'Central Cuts & Color',
            'Porter Hair Lounge', 'Kendall Style Studio', 'Fresh Pond Hair Design',
            'MIT Hair Salon', 'Inman Square Styles', 'Huron Hair & Beauty',
            'North Cambridge Salon', 'East Cambridge Hair', 'Riverside Hair Studio',
            'Cambridge Style House', 'Harvard Hair Design', 'Porter Hair & Spa'
        ],
        'barber': [
            'Cambridge Barber Co', 'Harvard Square Barbershop', 'Central Square Cuts',
            'Porter Barbershop', 'Kendall Barber', 'Fresh Pond Barber',
            'MIT Barbershop', 'Inman Square Barber', 'Huron Barber Shop',
            'North Cambridge Barber', 'East Cambridge Cuts', 'Riverside Barbershop',
            'Cambridge Classic Barber', 'Harvard Barber Shop', 'Porter Mens Grooming'
        ],
        'auto_mechanic': [
            'Cambridge Auto Repair', 'Harvard Square Auto', 'Central Auto Service',
            'Porter Auto Care', 'Kendall Car Repair', 'Fresh Pond Automotive',
            'MIT Auto Shop', 'Inman Auto Service', 'Huron Auto Repair',
            'North Cambridge Auto', 'East Cambridge Mechanics', 'Riverside Auto Care',
            'Cambridge Car Service', 'Harvard Auto Repair', 'Porter Auto Shop'
        ],
        'plumber': [
            'Cambridge Plumbing', 'Harvard Square Plumbers', 'Central Plumbing Services',
            'Porter Plumbing', 'Kendall Plumber', 'Fresh Pond Plumbing',
            'MIT Plumbing Service', 'Inman Plumbing Co', 'Huron Plumbers',
            'North Cambridge Plumbing', 'East Cambridge Plumber', 'Riverside Plumbing',
            'Cambridge Plumbing Pros', 'Harvard Plumbing', 'Porter Plumbing Services'
        ],
        'electrician': [
            'Cambridge Electric', 'Harvard Square Electric', 'Central Electric Services',
            'Porter Electric', 'Kendall Electrician', 'Fresh Pond Electric',
            'MIT Electric Service', 'Inman Electric Co', 'Huron Electricians',
            'North Cambridge Electric', 'East Cambridge Electrician', 'Riverside Electric',
            'Cambridge Electric Pros', 'Harvard Electric', 'Porter Electric Services'
        ],
        'massage': [
            'Cambridge Massage Therapy', 'Harvard Square Spa', 'Central Wellness Center',
            'Porter Massage', 'Kendall Massage Studio', 'Fresh Pond Spa',
            'MIT Wellness Center', 'Inman Massage Co', 'Huron Massage Therapy',
            'North Cambridge Spa', 'East Cambridge Massage', 'Riverside Wellness',
            'Cambridge Healing Touch', 'Harvard Massage Center', 'Porter Spa & Wellness'
        ],
        'veterinarian': [
            'Cambridge Veterinary', 'Harvard Square Animal Hospital', 'Central Pet Clinic',
            'Porter Vet Care', 'Kendall Animal Clinic', 'Fresh Pond Vet',
            'MIT Veterinary Service', 'Inman Animal Hospital', 'Huron Vet Clinic',
            'North Cambridge Vet', 'East Cambridge Animal Care', 'Riverside Veterinary',
            'Cambridge Pet Hospital', 'Harvard Vet Center', 'Porter Animal Clinic'
        ],
        'restaurant': [
            'Harvest Restaurant Cambridge', 'Alden & Harlow', 'Giulia Restaurant',
            'Pammy\'s Cambridge', 'Oleana Restaurant', 'Sarma Restaurant',
            'Catalyst Restaurant', 'Waypoint Harvard Square', 'Grendel\'s Den',
            'Life Alive Organic Cafe', 'Sulmona Restaurant', 'Bisq Restaurant',
            'The Urban Hearth', 'Rialto Restaurant', 'Russell House Tavern'
        ]
    }

    names = provider_data.get(service_type, provider_data['doctor'])
    test_number = os.getenv('TEST_CALL_NUMBER', '+16173596803')

    providers = []
    for i, name in enumerate(names[:2]):  # Testing with 2 providers
        providers.append({
            'name': name,
            'address': cambridge_addresses[i],
            'rating': round(random.uniform(4.0, 5.0), 1),
            'phone': test_number,  # All use the same test number
            'place_id': f'mock_place_{service_type}_{i}'
        })

    return providers


def make_real_calls(service_type, location, timeframe, booking_id=None):
    """Make real calls to providers using mock Cambridge data + Twilio"""
    try:
        print(f"🚀 REAL CALLING MODE: Finding providers and making calls...")

        # 1. Use mock Cambridge providers (to save Google API costs)
        providers = get_mock_cambridge_providers(service_type)

        if not providers:
            print(f"❌ No providers found for {service_type}")
            return []

        print(f"✅ Found {len(providers)} mock Cambridge providers")

        # 2. Mock distance data (Cambridge is small, all within 2-3 miles)
        distance_data = {}
        for provider in providers:
            distance_data[provider['address']] = {
                'distance_miles': round(random.uniform(0.3, 2.8), 1),
                'duration_minutes': random.randint(5, 15)
            }

        # Initialize all providers as pending if booking_id provided
        if booking_id:
            pending_results = []
            for provider in providers:
                pending_results.append({
                    'provider_id': provider.get('place_id', str(uuid.uuid4())),
                    'provider_name': provider['name'],
                    'phone': provider['phone'],
                    'address': provider['address'],
                    'rating': provider['rating'],
                    'call_status': 'pending'
                })
            db.update_booking_results(booking_id, pending_results)

        # 3. Use ElevenLabs for outbound calls when configured (we only call ElevenLabs API;
        #    ElevenLabs places the call via their own Twilio integration — we do not use our Twilio client).
        #    Fallback: if ElevenLabs agent/phone not set, use our Twilio client with scripted TwiML (no AI).
        use_elevenlabs_outbound = bool(
            os.getenv('ELEVENLABS_AGENT_ID') and os.getenv('ELEVENLABS_AGENT_PHONE_NUMBER_ID')
        )
        if use_elevenlabs_outbound:
            elevenlabs_service = get_elevenlabs_service()
        else:
            print("⚠️  ElevenLabs outbound not configured — set ELEVENLABS_AGENT_ID and ELEVENLABS_AGENT_PHONE_NUMBER_ID in .env to use AI calls. Using Twilio fallback.")
            twilio_service = get_twilio_service()  # fallback: scripted TwiML only

        # 4. Make calls to each provider (all to test number when USE_TEST_NUMBER=true)
        results = []
        booking_context = {
            'service_type': service_type,
            'timeframe': timeframe,
            'location': location,
            'client_name': 'Alberto Menendez',
        }

        to_number = providers[0]['phone']  # test number when using mock providers
        if use_elevenlabs_outbound:
            print(f"\n🎯 Using ElevenLabs Conversational AI (multi-turn) to: {to_number}\n")
        else:
            print(f"\n🎯 Making Twilio calls to test number: {to_number}\n")

        for i, provider in enumerate(providers, 1):
            print(f"📞 [{i}/{len(providers)}] Processing {provider['name']}...")

            # Update status to 'calling' for this provider (results so far + current as 'calling' + rest as 'pending')
            if booking_id:
                current_results = list(results)
                current_results.append({
                    'provider_id': provider.get('place_id', str(uuid.uuid4())),
                    'provider_name': provider['name'],
                    'phone': provider['phone'],
                    'address': provider['address'],
                    'rating': provider['rating'],
                    'call_status': 'calling'
                })
                for p in providers[i:]:
                    current_results.append({
                        'provider_id': p.get('place_id', str(uuid.uuid4())),
                        'provider_name': p['name'],
                        'phone': p['phone'],
                        'address': p['address'],
                        'rating': p['rating'],
                        'call_status': 'pending'
                    })
                db.update_booking_results(booking_id, current_results)

            if use_elevenlabs_outbound:
                print(f"🎯 Making ElevenLabs call to: {to_number}")
                call_info = elevenlabs_service.make_elevenlabs_outbound_call(
                    to_number=provider['phone'],
                    provider_name=provider.get('name', ''),
                    booking_context=booking_context,
                )
            else:
                print(f"🎯 Making Twilio call to test number: {to_number}")
                agent_prompt = f"""You are calling {provider['name']} to book a {service_type} appointment.
Request availability for {timeframe}.
Be professional and concise."""
                call_info = twilio_service.make_call(
                    to_number=provider['phone'],
                    agent_prompt=agent_prompt,
                    booking_context=booking_context,
                    provider_name=provider.get('name')
                )

            if call_info.get('status') not in ('failed', None):
                # Calculate score based on distance and rating
                dist_data = distance_data.get(provider['address'], {})
                distance_miles = dist_data.get('distance_miles', 1.5)
                travel_minutes = dist_data.get('duration_minutes', 10)

                # Score calculation: prioritize closer providers with good ratings
                distance_score = max(0, 50 - (distance_miles * 3))
                rating_score = provider['rating'] * 10
                base_score = distance_score + rating_score

                # Simulate availability (in production would parse call transcript)
                has_availability = random.random() < 0.7

                if has_availability:
                    days_out = random.randint(1, 10)
                    availability_date = (datetime.now() + timedelta(days=days_out)).strftime('%A, %B %d')
                    availability_time = random.choice(['9:00 AM', '10:30 AM', '2:00 PM', '3:30 PM', '4:00 PM'])

                    # Earlier appointments boost score
                    time_bonus = max(0, 30 - (days_out * 2))
                    final_score = min(98, base_score + time_bonus)
                else:
                    availability_date = "No availability"
                    availability_time = "-"
                    final_score = 0

                result = {
                    'provider_id': provider.get('place_id', str(uuid.uuid4())),
                    'provider_name': provider['name'],
                    'phone': provider['phone'],
                    'address': provider['address'],
                    'rating': provider['rating'],
                    'distance': distance_miles,
                    'travel_time': travel_minutes,
                    'availability_date': availability_date,
                    'availability_time': availability_time,
                    'score': int(final_score),
                    'call_sid': call_info.get('call_sid'),
                    'call_status': 'completed',
                    'has_availability': has_availability
                }
                results.append(result)

                # Update results progressively
                if booking_id:
                    current_results = list(results)
                    for p in providers[i:]:
                        current_results.append({
                            'provider_id': p.get('place_id', str(uuid.uuid4())),
                            'provider_name': p['name'],
                            'phone': p['phone'],
                            'address': p['address'],
                            'rating': p['rating'],
                            'call_status': 'pending'
                        })
                    db.update_booking_results(booking_id, current_results)

                print(f"   ✅ Call SID: {call_info.get('call_sid') or call_info.get('conversation_id')}")
                print(f"   📊 Score: {final_score:.0f} | Distance: {distance_miles:.1f}mi | Rating: {provider['rating']}⭐")
            else:
                result = {
                    'provider_id': provider.get('place_id', str(uuid.uuid4())),
                    'provider_name': provider['name'],
                    'phone': provider['phone'],
                    'address': provider['address'],
                    'rating': provider['rating'],
                    'call_status': 'failed'
                }
                results.append(result)

                # Update results with failed status
                if booking_id:
                    current_results = list(results)
                    for p in providers[i:]:
                        current_results.append({
                            'provider_id': p.get('place_id', str(uuid.uuid4())),
                            'provider_name': p['name'],
                            'phone': p['phone'],
                            'address': p['address'],
                            'rating': p['rating'],
                            'call_status': 'pending'
                        })
                    db.update_booking_results(booking_id, current_results)

                print(f"   ❌ Call failed: {call_info.get('error')}")

        # Sort by score
        results.sort(key=lambda x: x.get('score', 0), reverse=True)

        print(f"\n✅ Completed {len(results)} calls successfully")
        return results

    except Exception as e:
        print(f"❌ Error in make_real_calls: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


# Mock provider data generator
def generate_mock_results(service_type, location, booking_id=None):
    """Generate realistic mock appointment results with progressive updates"""

    # Service type to provider names mapping
    provider_templates = {
        'dentist': [
            'SmileCare Dental', 'Bright Teeth Family Dentistry', 'Advanced Dental Associates',
            'Comfort Dental Center', 'Elite Dental Group'
        ],
        'doctor': [
            'HealthFirst Medical Group', 'Primary Care Associates', 'WellCare Physicians',
            'Community Health Center', 'Family Medicine Clinic'
        ],
        'hair_salon': [
            'Style Studio', 'Hair Lounge', 'Glam & Co', 'The Cutting Room', 'Salon Luxe'
        ],
        'barber': [
            'Classic Cuts Barbershop', 'The Barber Club', 'Gentleman\'s Cut', 'Old School Barber', 'Modern Barber Co'
        ],
        'auto_mechanic': [
            'AutoCare Service Center', 'Precision Auto Repair', 'Quick Fix Auto', 'Master Mechanics', 'TrueCare Auto'
        ],
        'plumber': [
            '24/7 Plumbing Services', 'Pro Plumbing Solutions', 'Rapid Response Plumbing', 'Expert Plumbers Inc', 'A+ Plumbing'
        ],
        'electrician': [
            'Bright Spark Electric', 'Power Pro Electricians', 'Safe Wiring Solutions', 'Elite Electric Services', 'Current Electric'
        ],
        'massage': [
            'Zen Massage Therapy', 'Healing Hands Spa', 'Relaxation Station', 'Serenity Massage', 'Body & Soul Wellness'
        ],
        'veterinarian': [
            'PetCare Animal Hospital', 'Companion Vet Clinic', 'Paws & Claws Veterinary', 'Happy Pets Vet Center', 'Animal Health Clinic'
        ],
        'restaurant': [
            'Harvest Restaurant', 'Alden & Harlow', 'Giulia Restaurant', 'Pammy\'s Cambridge', 'Oleana Restaurant',
            'Sarma Restaurant', 'Craigie on Main', 'The Hourly Oyster House', 'Longfellow Bar', 'Parsnip Restaurant'
        ]
    }

    providers = provider_templates.get(service_type, provider_templates['doctor'])
    num_providers = min(5, len(providers))

    # Initialize all providers as pending if booking_id provided
    if booking_id:
        pending_results = []
        for i in range(num_providers):
            pending_results.append({
                'provider_id': str(uuid.uuid4()),
                'provider_name': providers[i],
                'phone': f'+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
                'address': f'{random.randint(100, 9999)} Main St, {location}',
                'rating': round(random.uniform(4.0, 5.0), 1),
                'call_status': 'pending'
            })
        db.update_booking_results(booking_id, pending_results)

    results = []
    for i, name in enumerate(providers[:num_providers]):
        # Simulate calling delay
        time.sleep(2)  # 2 second delay between calls

        # Update status to calling
        if booking_id:
            current_results = list(results)
            for j in range(i, num_providers):
                current_results.append({
                    'provider_id': str(uuid.uuid4()) if j > i else pending_results[i]['provider_id'],
                    'provider_name': providers[j],
                    'phone': pending_results[j]['phone'],
                    'address': pending_results[j]['address'],
                    'rating': pending_results[j]['rating'],
                    'call_status': 'calling' if j == i else 'pending'
                })
            db.update_booking_results(booking_id, current_results)

        # Generate realistic data
        days_out = random.randint(1, 14)
        availability_date = (datetime.now() + timedelta(days=days_out)).strftime('%A, %B %d')

        # Earlier appointments get better scores
        base_score = 95 - (days_out * 3)

        result = {
            'provider_id': pending_results[i]['provider_id'] if booking_id else str(uuid.uuid4()),
            'provider_name': name,
            'phone': pending_results[i]['phone'] if booking_id else f'+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}',
            'address': pending_results[i]['address'] if booking_id else f'{random.randint(100, 9999)} Main St, {location}',
            'rating': pending_results[i]['rating'] if booking_id else round(random.uniform(4.0, 5.0), 1),
            'distance': round(random.uniform(0.5, 8.0), 1),
            'travel_time': random.randint(5, 25),
            'availability_date': availability_date,
            'availability_time': random.choice(['9:00 AM', '10:30 AM', '2:00 PM', '3:30 PM', '4:00 PM']),
            'score': min(98, base_score + random.randint(-5, 5)),
            'call_status': 'completed'
        }
        results.append(result)

        # Update with completed call
        if booking_id:
            current_results = list(results)
            for j in range(i + 1, num_providers):
                current_results.append({
                    'provider_id': pending_results[j]['provider_id'],
                    'provider_name': providers[j],
                    'phone': pending_results[j]['phone'],
                    'address': pending_results[j]['address'],
                    'rating': pending_results[j]['rating'],
                    'call_status': 'pending'
                })
            db.update_booking_results(booking_id, current_results)

    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)

    return results

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'callpilot'}), 200


def _twilio_voice_twiml(step, service_type, timeframe, provider_name, webhook_base_url, speech_result=None, client_name="Alberto Menendez"):
    """Build multi-turn TwiML: step 0 = greet + gather, step 1 = follow-up + gather, step 2 = thank + hangup."""
    from urllib.parse import urlencode
    step = int(step) if step is not None else 0
    base_params = {
        'service_type': service_type or 'appointment',
        'timeframe': timeframe or 'this week',
        'provider_name': provider_name or 'the business',
        'client_name': client_name or 'Alberto Menendez',
    }
    action_url_1 = f"{webhook_base_url.rstrip('/')}/api/twilio/voice?{urlencode({**base_params, 'step': 1})}"
    action_url_2 = f"{webhook_base_url.rstrip('/')}/api/twilio/voice?{urlencode({**base_params, 'step': 2})}"
    name = client_name or "Alberto Menendez"
    st = (service_type or "appointment").replace("_", " ")
    tf = (timeframe or "this week").replace("_", " ")

    if step == 0:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">
        Hello, this is Call Pilot. I'm calling on behalf of {name} to book a {st} appointment. He's looking for something {tf}. Are you the right person to schedule that?
    </Say>
    <Pause length="1"/>
    <Say voice="Polly.Matthew">Please say when you have openings, or press any key to continue.</Say>
    <Gather input="speech dtmf" action="{action_url_1}" method="POST" timeout="10" speechTimeout="5" language="en-US" numDigits="1">
    </Gather>
    <Say voice="Polly.Matthew">We didn't catch that. I'll note you may need to call back. Thank you, goodbye.</Say>
    <Hangup/>
</Response>'''
    if step == 1:
        # Follow-up: ask for specific times so we don't hang up after one exchange
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">Thanks. What specific date or time works best? Or should we call back to confirm?</Say>
    <Gather input="speech dtmf" action="{action_url_2}" method="POST" timeout="10" speechTimeout="5" language="en-US" numDigits="1">
    </Gather>
    <Say voice="Polly.Matthew">Got it. We'll follow up to confirm. Thank you, goodbye.</Say>
    <Hangup/>
</Response>'''
    # step == 2: thank and close
    response_ack = "Thank you for that information." if speech_result else "Thank you."
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew">
        {response_ack} I've noted it. We'll confirm the appointment and call back if needed. Goodbye.
    </Say>
    <Hangup/>
</Response>'''


@app.route('/api/twilio/voice', methods=['GET', 'POST'])
def twilio_voice_webhook():
    """
    Twilio voice webhook for multi-turn calls.
    Set TWILIO_WEBHOOK_BASE_URL to your public URL (e.g. ngrok) so Twilio can reach this.
    """
    step = request.args.get('step') or request.form.get('step')
    service_type = request.args.get('service_type') or request.form.get('service_type', 'appointment')
    timeframe = request.args.get('timeframe') or request.form.get('timeframe', 'this week')
    provider_name = request.args.get('provider_name') or request.form.get('provider_name', '')
    client_name = request.args.get('client_name') or request.form.get('client_name', 'Alberto Menendez')
    speech_result = request.form.get('SpeechResult') or request.form.get('Digits')
    webhook_base = os.getenv('TWILIO_WEBHOOK_BASE_URL', request.url_root.rstrip('/'))
    if not webhook_base or webhook_base == 'http://localhost:8080/':
        webhook_base = os.getenv('TWILIO_WEBHOOK_BASE_URL', '')
    if not webhook_base:
        webhook_base = request.url_root.rstrip('/')

    twiml = _twilio_voice_twiml(step, service_type, timeframe, provider_name, webhook_base, speech_result, client_name)
    from flask import Response
    return Response(twiml, mimetype='application/xml')


# --- Task + GenAI Chat (inbound info gathering) ---
from services.chat_service import chat as chat_service_chat

@app.route('/api/task', methods=['POST'])
def create_task():
    """Create a new task (one conversation = one task)."""
    try:
        task_id = str(uuid.uuid4())
        db.create_task(task_id)
        return jsonify({'task_id': task_id, 'status': 'gathering_info'}), 200
    except Exception as e:
        print(f"❌ Error creating task: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Send a message in a task conversation. Uses GenAI (Gemini or OpenAI) to reply
    and extract service_type, location, timeframe. Task status can be gathering_info,
    ready_to_call, or requires_user_attention.
    """
    try:
        data = request.json or {}
        task_id = data.get('task_id')
        message = (data.get('message') or '').strip()
        if not task_id:
            return jsonify({'error': 'task_id required'}), 400
        if not message:
            return jsonify({'error': 'message required'}), 400

        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        if task['status'] not in ('gathering_info', 'requires_user_attention'):
            return jsonify({'error': f'Task cannot accept messages in status {task["status"]}'}), 400

        # Append user message
        conv = list(task['conversation'])
        conv.append({'role': 'user', 'content': message})
        extracted = dict(task['extracted_data'])

        # Get AI reply and updated extraction
        reply, extracted, status = chat_service_chat(conv, extracted)

        # Append assistant reply
        conv.append({'role': 'assistant', 'content': reply})
        db.update_task(task_id, status=status, extracted_data=extracted, conversation=conv)

        return jsonify({
            'reply': reply,
            'extracted_data': extracted,
            'task_status': status,
            'task_id': task_id,
        }), 200
    except Exception as e:
        print(f"❌ Error in chat: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/task/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get task by id."""
    try:
        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Booking request endpoint
@app.route('/api/booking/request', methods=['POST'])
def create_booking_request():
    """
    Create a new booking request
    Expected payload:
    {
        "service_type": "dentist",
        "timeframe": "this week",
        "location": "user location",
        "preferences": {}
    }
    """
    try:
        data = request.json
        service_type = data.get('service_type')
        location = data.get('location')
        timeframe = data.get('timeframe')
        preferences = data.get('preferences', {})

        # Generate unique booking ID
        booking_id = str(uuid.uuid4())

        # Store booking in database
        db.create_booking(booking_id, service_type, location, timeframe, preferences)

        print(f"📞 Created booking {booking_id} for {service_type} in {location}")

        # Start provider calls in background so they run immediately (don't wait for polling)
        use_real_calls = os.getenv('USE_REAL_CALLS', 'false').lower() == 'true'

        def run_calls():
            try:
                if use_real_calls:
                    results = make_real_calls(service_type, location, timeframe, booking_id)
                else:
                    results = generate_mock_results(service_type, location, booking_id)
                db.update_booking_status(booking_id, 'completed', results)
                print(f"✅ Booking {booking_id} completed with {len(results)} results")
            except Exception as e:
                print(f"❌ Background calls failed for {booking_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.update_booking_status(booking_id, 'completed', [])

        thread = threading.Thread(target=run_calls, daemon=True)
        thread.start()

        return jsonify({
            'status': 'processing',
            'booking_id': booking_id,
            'message': 'Your booking request is being processed'
        }), 200

    except Exception as e:
        print(f"❌ Error creating booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Get booking status endpoint
@app.route('/api/booking/<booking_id>', methods=['GET'])
def get_booking_status(booking_id):
    """Get status of a booking request (calls are started in background at create time)"""
    try:
        booking = db.get_booking(booking_id)

        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        message = 'AI agents are calling providers...' if booking['status'] == 'processing' else None
        return jsonify({
            'booking_id': booking_id,
            'status': booking['status'],
            'results': booking.get('results', []),
            **({'message': message} if message else {})
        }), 200

    except Exception as e:
        print(f"❌ Error getting booking status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Confirm booking endpoint
@app.route('/api/booking/<booking_id>/confirm', methods=['POST'])
def confirm_booking(booking_id):
    """Confirm a selected booking option"""
    try:
        data = request.json
        provider_id = data.get('provider_id')

        booking = db.get_booking(booking_id)

        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        # Find the selected provider
        selected_provider = None
        for result in booking.get('results', []):
            if result['provider_id'] == provider_id:
                selected_provider = result
                break

        if not selected_provider:
            return jsonify({'error': 'Provider not found'}), 404

        print(f"✅ Confirmed booking {booking_id} with {selected_provider['provider_name']}")
        print(f"   📅 {selected_provider['availability_date']} at {selected_provider['availability_time']}")

        # In production: Call provider to confirm, add to calendar

        return jsonify({
            'status': 'confirmed',
            'booking_id': booking_id,
            'provider': selected_provider,
            'message': f'Booking confirmed at {selected_provider["provider_name"]}!',
            'calendar_event_id': str(uuid.uuid4())
        }), 200

    except Exception as e:
        print(f"❌ Error confirming booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Dashboard endpoint - get all bookings and stats
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        bookings_list = db.get_all_bookings()
        total_bookings = len(bookings_list)
        completed = sum(1 for b in bookings_list if b['status'] == 'completed')
        processing = sum(1 for b in bookings_list if b['status'] == 'processing')

        # Calculate total calls made
        total_calls = sum(len(b.get('results', [])) for b in bookings_list)

        # Get recent bookings
        recent_bookings = sorted(
            bookings_list,
            key=lambda x: x['created_at'],
            reverse=True
        )[:10]

        return jsonify({
            'stats': {
                'total_bookings': total_bookings,
                'completed': completed,
                'processing': processing,
                'total_calls_made': total_calls,
                'success_rate': (completed / total_bookings * 100) if total_bookings > 0 else 0
            },
            'recent_bookings': recent_bookings
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Connections endpoint
@app.route('/api/connections', methods=['GET'])
def get_connections():
    """Get status of all connections"""
    try:
        use_real_calls = os.getenv('USE_REAL_CALLS', 'false').lower() == 'true'

        connections = {
            'twilio': {
                'name': 'Twilio Phone',
                'status': 'connected' if os.getenv('TWILIO_ACCOUNT_SID') else 'disconnected',
                'description': 'Real phone calling infrastructure'
            },
            'elevenlabs': {
                'name': 'ElevenLabs Voice AI',
                'status': 'connected' if os.getenv('ELEVENLABS_API_KEY') else 'disconnected',
                'description': 'AI voice agents (prompts only in this demo)'
            },
            'providers_database': {
                'name': 'Provider Database',
                'status': 'connected',
                'description': 'Mock Cambridge, MA providers (15 per category)'
            },
            'google_calendar': {
                'name': 'Google Calendar',
                'status': 'disconnected',
                'description': 'Calendar integration (future feature)'
            },
            'web_scraping': {
                'name': 'Web Scraping',
                'status': 'disconnected',
                'description': 'Provider website scraping (future feature)'
            }
        }

        return jsonify({'connections': connections}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get all bookings for dashboard
@app.route('/api/dashboard/bookings', methods=['GET'])
def get_all_bookings():
    """Get all bookings for dashboard view"""
    try:
        bookings_list = db.get_all_bookings()
        return jsonify({'bookings': bookings_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Admin: clean database (bookings + tasks)
@app.route('/api/admin/clean-db', methods=['POST'])
def admin_clean_db():
    """Clear all bookings and tasks. Use for development/reset."""
    try:
        db.clean_db()
        return jsonify({'ok': True, 'message': 'Database cleaned'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Text-to-Speech endpoint using ElevenLabs
@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech using ElevenLabs for natural voice"""
    try:
        data = request.json
        text = data.get('text')
        voice_id = data.get('voice_id', 'EXAVITQu4vr4xnSDxMaL')  # Sarah - natural female voice

        if not text:
            return jsonify({'error': 'Text is required'}), 400

        # Check if ElevenLabs is configured
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("⚠️  ElevenLabs API key not configured - TTS disabled")
            return jsonify({'error': 'ElevenLabs not configured'}), 503

        from elevenlabs.client import ElevenLabs
        from flask import Response

        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=api_key)

        # Generate audio using ElevenLabs
        print(f"🎤 Generating TTS for: {text[:50]}...")
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_monolingual_v1"
        )

        # Convert generator to bytes
        audio_bytes = b"".join(audio_generator)
        print(f"✅ TTS generated successfully ({len(audio_bytes)} bytes)")

        # Return audio as response
        return Response(audio_bytes, mimetype='audio/mpeg')

    except ImportError as e:
        print(f"❌ ElevenLabs library not installed: {str(e)}")
        return jsonify({'error': 'ElevenLabs library not available'}), 503
    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f"🚀 CallPilot Backend starting on port {port}")

    # Check if real calling is enabled
    use_real_calls = os.getenv('USE_REAL_CALLS', 'false').lower() == 'true'

    print(f"\n📊 Mode Configuration:")
    if use_real_calls:
        print(f"   🎯 REAL TWILIO CALLS enabled")
        print(f"   📍 Using mock Cambridge, MA providers (no Google API costs)")
        test_number = os.getenv('TEST_CALL_NUMBER')
        print(f"   📞 All calls route to: {test_number}")
    else:
        print(f"   🎭 DEMO MODE (fully simulated, no real calls)")

    print(f"\n🔧 Configured APIs:")
    print(f"   - Twilio: {'✅' if os.getenv('TWILIO_ACCOUNT_SID') else '❌'}")
    print(f"   - ElevenLabs: {'✅' if os.getenv('ELEVENLABS_API_KEY') else '❌'}")

    print(f"")
    app.run(host='0.0.0.0', port=port, debug=True)
