from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

def search_places(location, place_type):
    """Search for places using Google Places API"""
    if not GOOGLE_MAPS_API_KEY:
        # Return mock data if no API key
        return get_mock_places(location, place_type)
    
    try:
        # Geocode location to get coordinates
        geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
        geo_params = {'address': location, 'key': GOOGLE_MAPS_API_KEY}
        geo_response = requests.get(geo_url, params=geo_params)
        geo_data = geo_response.json()
        
        if not geo_data.get('results'):
            return get_mock_places(location, place_type)
        
        coords = geo_data['results'][0]['geometry']['location']
        
        # Search for places
        type_map = {'restaurant': 'restaurant', 'hotel': 'lodging', 'attraction': 'tourist_attraction'}
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        places_params = {
            'location': f"{coords['lat']},{coords['lng']}",
            'radius': 5000,
            'type': type_map.get(place_type, 'restaurant'),
            'key': GOOGLE_MAPS_API_KEY
        }
        
        places_response = requests.get(places_url, params=places_params)
        places_data = places_response.json()
        
        results = []
        for place in places_data.get('results', [])[:5]:
            results.append({
                'name': place.get('name'),
                'rating': place.get('rating', 'N/A'),
                'address': place.get('vicinity', 'Address not available'),
                'price': '$' * place.get('price_level', 0) if place.get('price_level') else 'N/A'
            })
        
        return results if results else get_mock_places(location, place_type)
        
    except Exception as e:
        print(f"Error: {e}")
        return get_mock_places(location, place_type)

def get_mock_places(location, place_type):
    """Return mock data for testing"""
    mock_data = {
        'restaurant': [
            {'name': f'Le Petit Cafe {location}', 'rating': 4.5, 'address': f'123 Main St, {location}', 'price': '$$'},
            {'name': f'Pizza Heaven {location}', 'rating': 4.2, 'address': f'456 Oak Ave, {location}', 'price': '$'},
            {'name': f'Sushi Master {location}', 'rating': 4.8, 'address': f'789 Pine Rd, {location}', 'price': '$$$'}
        ],
        'hotel': [
            {'name': f'Grand {location} Hotel', 'rating': 4.7, 'address': f'1 Hotel Blvd, {location}', 'price': '$$$'},
            {'name': f'Budget Inn {location}', 'rating': 3.9, 'address': f'100 Economy Ln, {location}', 'price': '$'}
        ],
        'attraction': [
            {'name': f'{location} Museum', 'rating': 4.6, 'address': f'200 Culture St, {location}', 'price': '$$'},
            {'name': f'{location} Park', 'rating': 4.4, 'address': f'300 Nature Dr, {location}', 'price': 'Free'}
        ]
    }
    return mock_data.get(place_type, mock_data['restaurant'])

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        
        # Simple intent detection
        if any(word in message for word in ['hi', 'hello', 'hey']):
            return jsonify({'response': 'Hello! 👋 I\'m TravelMate. Ask me to find restaurants, hotels, or attractions anywhere in the world! 🌍'})
        
        elif any(word in message for word in ['find', 'search', 'where', 'show']):
            # Detect place type
            place_type = 'restaurant'
            if 'hotel' in message or 'stay' in message:
                place_type = 'hotel'
            elif 'attraction' in message or 'tourist' in message or 'sight' in message:
                place_type = 'attraction'
            
            # Extract location
            location = None
            cities = ['paris', 'london', 'tokyo', 'new york', 'bali', 'sydney', 'rome', 'dubai', 'bangkok']
            for city in cities:
                if city in message:
                    location = city.title()
                    break
            
            if not location and 'near me' not in message:
                return jsonify({'response': f'📍 Which city would you like to find {place_type}s in? (e.g., Paris, London, Tokyo)'})
            
            if not location:
                location = "your area"
            
            # Search for places
            places = search_places(location, place_type)
            
            if places:
                response = f"✨ Found {len(places)} great {place_type}s in {location}! ✨\n\n"
                for i, place in enumerate(places, 1):
                    response += f"{i}. **{place['name']}**\n"
                    response += f"   ⭐ Rating: {place['rating']} | 💰 {place['price']}\n"
                    response += f"   📍 {place['address']}\n\n"
                response += "Would you like more details about any of these? Just ask! 🎯"
            else:
                response = f"😅 I couldn't find any {place_type}s in {location}. Try a different city or type of place!"
            
            return jsonify({'response': response})
        
        elif any(word in message for word in ['help', 'what can you do']):
            return jsonify({'response': '💡 I can help you:\n• Find restaurants 🍕\n• Book hotels 🏨\n• Discover attractions 🎯\n• Get travel tips ✈️\n\nJust tell me what you\'re looking for and where!'})
        
        else:
            return jsonify({'response': '🌟 I\'m here to help you travel better! Try asking:\n\n• "Find restaurants in Paris"\n• "Show me hotels in Tokyo"\n• "Find attractions near me"\n\nWhat would you like to explore? 🗺️'})
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'response': 'Sorry, something went wrong. Please try again! 🌍'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
