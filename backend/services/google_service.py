"""
Google Services Integration
Handles Google Calendar, Places, and Maps API calls
"""
import os
from typing import Dict, List
import googlemaps
import requests

class GoogleService:
    """Service for Google API integrations"""

    def __init__(self):
        self.places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

        if not self.places_api_key or not self.maps_api_key:
            raise ValueError("Google API keys not found in environment variables")

        self.gmaps = googlemaps.Client(key=self.maps_api_key)
        print(f"✅ Google services initialized")

    def find_providers(self, service_type: str, location: str, radius: int = 16000) -> List[Dict]:
        """
        Find service providers using Google Places API

        Args:
            service_type: Type of service (e.g., 'dentist', 'hair salon')
            location: User's location
            radius: Search radius in meters (default 10 miles = 16000m)

        Returns:
            providers: List of provider information
        """
        try:
            print(f"🔍 Searching for {service_type} near {location}...")

            # Geocode the location first
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                print(f"❌ Could not geocode location: {location}")
                return []

            lat = geocode_result[0]['geometry']['location']['lat']
            lng = geocode_result[0]['geometry']['location']['lng']

            # Map service types to Google Places types
            service_type_mapping = {
                'dentist': 'dentist',
                'doctor': 'doctor',
                'hair_salon': 'hair_care',
                'barber': 'hair_care',
                'auto_mechanic': 'car_repair',
                'plumber': 'plumber',
                'electrician': 'electrician',
                'massage': 'spa',
                'veterinarian': 'veterinary_care'
            }

            places_type = service_type_mapping.get(service_type, service_type)

            # Search for places
            places_result = self.gmaps.places_nearby(
                location=(lat, lng),
                radius=radius,
                type=places_type
            )

            providers = []
            for place in places_result.get('results', [])[:15]:  # Limit to 15 providers
                # Get place details for phone number
                place_details = self.gmaps.place(place['place_id'])

                provider = {
                    'name': place.get('name', 'Unknown'),
                    'address': place.get('vicinity', ''),
                    'rating': place.get('rating', 0.0),
                    'phone': place_details.get('result', {}).get('formatted_phone_number', 'N/A'),
                    'place_id': place['place_id']
                }
                providers.append(provider)

            print(f"✅ Found {len(providers)} providers")
            return providers

        except Exception as e:
            print(f"❌ Error finding providers: {str(e)}")
            return []

    def get_distance_matrix(self, origin: str, destinations: List[str]) -> Dict:
        """
        Calculate distances and travel times to multiple destinations

        Args:
            origin: User's location
            destinations: List of provider addresses

        Returns:
            distance_data: Distance and duration information for each destination
        """
        try:
            if not destinations:
                return {}

            result = self.gmaps.distance_matrix(
                origins=[origin],
                destinations=destinations,
                mode='driving',
                units='imperial'
            )

            distance_data = {}
            for i, dest in enumerate(destinations):
                element = result['rows'][0]['elements'][i]
                if element['status'] == 'OK':
                    distance_data[dest] = {
                        'distance_miles': element['distance']['value'] / 1609.34,  # Convert to miles
                        'duration_minutes': element['duration']['value'] / 60  # Convert to minutes
                    }

            return distance_data

        except Exception as e:
            print(f"❌ Error calculating distances: {str(e)}")
            return {}

    def check_calendar_availability(self, user_id: str, time_slots: List[Dict]) -> List[bool]:
        """
        Check if proposed time slots conflict with user's calendar

        Args:
            user_id: User identifier
            time_slots: List of proposed appointment times

        Returns:
            availability: List of booleans indicating availability
        """
        # For now, return all slots as available
        # In production, would integrate with Google Calendar API
        return [True] * len(time_slots)

    def add_to_calendar(self, user_id: str, appointment: Dict) -> bool:
        """
        Add confirmed appointment to user's Google Calendar

        Args:
            user_id: User identifier
            appointment: Appointment details

        Returns:
            success: Boolean indicating if event was added
        """
        # In production, would use Google Calendar API to create event
        print(f"📅 Would add to calendar: {appointment}")
        return True


# Singleton instance
_google_service = None

def get_google_service() -> GoogleService:
    """Get or create the Google service singleton"""
    global _google_service
    if _google_service is None:
        _google_service = GoogleService()
    return _google_service
