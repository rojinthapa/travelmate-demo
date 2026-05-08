from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
from places_api import PlacesAPI
import google.generativeai as genai
import json

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)

# Initialize Places API
places_api = PlacesAPI()

# Initialize Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    gemini_available = True
    logger.info("Gemini AI initialized successfully")
else:
    gemini_available = False
    logger.warning("Gemini API key not found, using fallback responses")

# Serve HTML files
@app.route('/')
def serve_index():
    return send_from_directory('..', 'index.html')

@app.route('/chat.html')
def serve_chat():
    return send_from_directory('..', 'chat.html')

# Serve static files
@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory('../css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('../js', path)

@app.route('/images/<path:path>')
def serve_images(path):
    return send_from_directory('../images', path)

def process_with_gemini(user_message):
    """Use Gemini AI to understand user intent"""
    prompt = f"""
    You are TravelMate, an AI travel assistant. Analyze this user message and return ONLY valid JSON (no other text):
    
    User message: "{user_message}"
    
    Return this exact JSON format:
    {{
        "intent": "greeting or find_places or help or unknown",
        "place_type": "restaurant or hotel or attraction or null",
        "location": "city name or null",
        "friendly_response": "a short, friendly reply to the user"
    }}
    
    Examples:
    User: "Find restaurants in Paris"
    Return: {{"intent": "find_places", "place_type": "restaurant", "location": "Paris", "friendly_response": "Searching for restaurants in Paris! 🍽️"}}
    
    User: "Hello"
    Return: {{"intent": "greeting", "place_type": null, "location": null, "friendly_response": "Hello! I'm TravelMate, your AI travel assistant. How can I help you today? ✈️"}}
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        # Clean the response (remove any markdown code blocks)
        clean_response = response.text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response.replace('```json', '').replace('```', '')
        if clean_response.startswith('```'):
            clean_response = clean_response.replace('```', '')
        
        result = json.loads(clean_response)
        return result
    except Exception as e:
        logger.error(f"Gemini error: {str(e)}")
        return None

def fallback_response(user_message):
    """Simple fallback if Gemini is not available"""
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ['hi', 'hello', 'hey']):
        return {"intent": "greeting", "place_type": None, "location": None, "friendly_response": "Hello! I'm TravelMate, your AI travel assistant. How can I help you today? ✈️"}
    
    elif any(word in message_lower for word in ['find', 'search', 'where']):
        place_type = "restaurant"
        if 'hotel' in message_lower:
            place_type = "hotel"
        elif 'attraction' in message_lower:
            place_type = "attraction"
        
        cities = ['paris', 'london', 'tokyo', 'new york', 'bali', 'sydney']
        location = None
        for city in cities:
            if city in message_lower:
                location = city.title()
                break
        
        if location:
            return {"intent": "find_places", "place_type": place_type, "location": location, "friendly_response": f"Searching for {place_type}s in {location}! 🗺️"}
        else:
            return {"intent": "find_places", "place_type": place_type, "location": None, "friendly_response": f"Which city would you like to find {place_type}s in?"}
    
    else:
        return {"intent": "unknown", "place_type": None, "location": None, "friendly_response": "I can help you find restaurants, hotels, and attractions. Try saying 'Find restaurants in Paris' or 'Show me hotels in Tokyo' 🗺️"}

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message']
        logger.info(f"Received: {user_message}")
        
        # Try Gemini first, fallback to simple NLP
        if gemini_available:
            ai_result = process_with_gemini(user_message)
        else:
            ai_result = None
        
        if not ai_result:
            ai_result = fallback_response(user_message)
        
        intent = ai_result.get('intent', 'unknown')
        place_type = ai_result.get('place_type')
        location = ai_result.get('location')
        friendly_response = ai_result.get('friendly_response', "How can I help you?")
        
        # If user wants to find places and has location
        if intent == 'find_places' and location and place_type:
            # Search using Google Places API
            places = places_api.search_places(location, place_type)
            
            if places and len(places) > 0:
                # Format places response
                places_text = f"\n\n📍 **Top {place_type}s in {location}:**\n\n"
                for i, place in enumerate(places[:5], 1):
                    places_text += f"{i}. **{place['name']}**\n"
                    if place.get('rating') and place['rating'] != 'N/A':
                        places_text += f"   ⭐ Rating: {place['rating']}\n"
                    places_text += f"   📍 {place['address']}\n"
                    if place.get('price') and place['price'] != 'N/A':
                        places_text += f"   💰 {place['price']}\n"
                    places_text += "\n"
                
                places_text += "Would you like more details about any of these?"
                full_response = friendly_response + places_text
            else:
                full_response = f"I couldn't find any {place_type}s in {location}. Try a different city or type of place! 🌍"
        else:
            full_response = friendly_response
        
        return jsonify({
            'response': full_response,
            'intent': intent,
            'gemini_used': gemini_available and ai_result is not None
        })
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'response': f"Sorry, I encountered an error: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'gemini': gemini_available})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
