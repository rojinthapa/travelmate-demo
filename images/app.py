from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
from nlp_processor import NLPProcessor
from places_api import PlacesAPI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize processors
nlp_processor = NLPProcessor()
places_api = PlacesAPI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/api/set_location', methods=['POST'])
def set_location():
    try:
        data = request.get_json()
        if not data or 'location' not in data:
            return jsonify({'error': 'No location provided'}), 400

        location = data['location']
        nlp_processor.set_current_location(location)
        logger.info(f"User location set to: {location}")
        
        return jsonify({
            'message': f'Location set to {location}',
            'location': location
        })

    except Exception as e:
        logger.error(f"Error setting location: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_message = data['message']
        logger.info(f"Received message: {user_message}")

        # Process the message using NLP
        intent, entities = nlp_processor.process_message(user_message)
        logger.info(f"Processed intent: {intent}, entities: {entities}")

        # Handle location required case
        if intent == 'location_required':
            return jsonify({
                'response': entities['message'],
                'intent': intent,
                'entities': entities
            })

        # Generate response based on intent and entities
        response = generate_response(intent, entities, user_message)
        logger.info(f"Generated response: {response}")

        return jsonify({
            'response': response,
            'intent': intent,
            'entities': entities
        })

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def generate_response(intent, entities, original_message):
    """
    Generate a response based on the intent and entities
    """
    try:
        if intent == 'greeting':
            return "Hello! I'm your TravelMate assistant. How can I help you today?"

        elif intent == 'help':
            return "I can help you find restaurants, hotels, and attractions. Just tell me what you're looking for and where!"

        elif intent == 'find_places':
            if not entities.get('location'):
                return "Could you please specify a location? For example, 'Find restaurants in Paris'"
            
            location = entities['location']
            place_type = entities.get('place_type', 'restaurant')
            
            # Search for places
            places = places_api.search_places(location, place_type)
            logger.info(f"Found {len(places)} places in {location}")
            
            if not places:
                return f"I couldn't find any {place_type}s . Would you like to try a different location or type of place?"
            
            # Format the response
            response = f"Here are some {place_type}s in {location}:\n\n"
            for i, place in enumerate(places[:5], 1):
                response += f"{i}. {place['name']}\n"
                if place['rating'] != 'N/A':
                    response += f"   Rating: {place['rating']} ⭐\n"
                if place['price'] != 'N/A':
                    response += f"   Price: {place['price']}\n"
                response += f"   Address: {place['address']}\n"
                if place['is_closed']:
                    response += "   ⚠️ Currently closed\n"
                response += "\n"
            
            response += "Would you like more details about any of these places? Just ask for the place number (1-5)."
            return response

        elif intent == 'get_info':
            if not entities.get('place_type'):
                return "What kind of information would you like? I can tell you about restaurants, hotels, or attractions."
            
            place_type = entities['place_type']
            return f"I can help you find information about {place_type}s. What specific details would you like to know?"

        else:
            return "I'm not sure I understand. Could you please rephrase that? I can help you find places or provide information about destinations."

    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "I apologize, but I encountered an error. Could you please try again?"

if __name__ == '__main__':
    app.run(debug=True) 
 