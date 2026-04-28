import os
from dotenv import load_dotenv
import requests
import logging
from typing import Dict, List, Optional



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Get the directory where the current script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the .env file inside the same directory
env_path = os.path.join(current_dir, ".env")

# Load the .env file
load_dotenv(dotenv_path=env_path)

class PlacesAPI:
    def __init__(self, api_key: Optional[str] = None):
        # self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.api_key = "AIzaSyCDCnLGFUP9tONtVQl1KfXzAxW0AJLbDps";
        if not self.api_key:
            raise ValueError("Google Maps API key is required")
        print("API Key:", self.api_key)

        logger.info("PlacesAPI initialized successfully")
        
        # Define place type mappings for Google Places API
        self.place_type_mappings = {
            "restaurant": "restaurant",
            "cafe": "cafe",
            "bar": "bar",
            "hotel": "lodging",
            "attraction": "tourist_attraction",
            "museum": "museum",
            "park": "park"
        }
    
    def get_coordinates(self, location: str) -> Dict[str, float]:
        """
        Get coordinates for a location using Google Geocoding API
        """
        try:
            base_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': location,
                'key': self.api_key
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lng': location['lng']
                }
            else:
                logger.error(f"Geocoding error for {location}: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting coordinates: {str(e)}")
            return None
    
    def search_places(self, location: str, place_type: str, radius: int = 5000) -> List[Dict]:
        """
        Search for places using Google Places API
        """
        try:
            logger.info(f"Searching for {place_type} in {location}")
            
            # Get coordinates for the location
            location_coords = self.get_coordinates(location)
            if not location_coords:
                logger.error(f"Could not find coordinates for location: {location}")
                return []
            
            # Get category from map, default to 'restaurant' if not found
            category = self.place_type_mappings.get(place_type.lower(), 'restaurant')
            logger.info(f"Using Google Places category: {category}")
            
            # Construct the Places API URL
            base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{location_coords['lat']},{location_coords['lng']}",
                'radius': radius,
                'type': category,
                'key': self.api_key
            }
            
            # Make the API request
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Places API error: {data.get('status')}")
                return []
            
            # Format results
            places = []
            for place in data.get('results', []):
                place_info = {
                    'name': place.get('name'),
                    'rating': place.get('rating', 'N/A'),
                    'price': self._get_price_level(place.get('price_level')),
                    'address': place.get('vicinity', 'N/A'),
                    'phone': 'N/A',  # Would need additional API call for phone
                    'url': f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}",
                    'image_url': self._get_photo_url(place.get('photos', [])),
                    'is_closed': place.get('business_status') == 'CLOSED_TEMPORARILY',
                    'place_id': place.get('place_id')
                }
                places.append(place_info)
            
            logger.info(f"Found {len(places)} places")
            return places
            
        except Exception as e:
            logger.error(f"Error searching places: {str(e)}")
            return []
    
    def _get_price_level(self, price_level: Optional[int]) -> str:
        """
        Convert Google Places price level to readable format
        """
        if price_level is None:
            return 'N/A'
        return '$' * price_level
    
    def _get_photo_url(self, photos: List[Dict]) -> str:
        """
        Get photo URL from Google Places photo reference
        """
        if not photos:
            return ''
        photo_reference = photos[0].get('photo_reference')
        if not photo_reference:
            return ''
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={self.api_key}"
    
    def get_place_details(self, place_id: str) -> Dict:
        """
        Get detailed information about a specific place
        """
        try:
            logger.info(f"Getting details for place ID: {place_id}")
            base_url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                'place_id': place_id,
                'fields': 'name,rating,price_level,formatted_address,formatted_phone_number,website,photos,opening_hours,reviews',
                'key': self.api_key
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"Places API error: {data.get('status')}")
                return None
            
            result = data.get('result', {})
            return {
                'name': result.get('name'),
                'rating': result.get('rating'),
                'price': self._get_price_level(result.get('price_level')),
                'address': result.get('formatted_address'),
                'phone': result.get('formatted_phone_number'),
                'url': result.get('website'),
                'image_url': self._get_photo_url(result.get('photos', [])),
                'is_closed': not result.get('opening_hours', {}).get('open_now', True),
                'hours': result.get('opening_hours', {}).get('weekday_text', []),
                'reviews': result.get('reviews', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")
            return None 




