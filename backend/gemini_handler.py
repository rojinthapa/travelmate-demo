import google.generativeai as genai
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GeminiHandler:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.available = False
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.available = True
                logger.info("Gemini AI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        else:
            logger.warning("GEMINI_API_KEY not found. Gemini features disabled.")
    
    def process_message(self, user_message):
        """Use Gemini to understand user intent and generate response"""
        if not self.available:
            return None
        
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
        
        User: "I want a hotel in Tokyo"
        Return: {{"intent": "find_places", "place_type": "hotel", "location": "Tokyo", "friendly_response": "Looking for hotels in Tokyo! 🏨"}}
        """
        
        try:
            response = self.model.generate_content(prompt)
            clean_response = response.text.strip()
            
            # Remove markdown code blocks if present
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '')
            if clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '')
            
            result = json.loads(clean_response)
            return result
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None
    
    def enhance_response(self, user_message, places_data):
        """Use Gemini to create a natural, conversational response with place data"""
        if not self.available or not places_data:
            return None
        
        places_text = ""
        for i, place in enumerate(places_data[:5], 1):
            places_text += f"{i}. {place.get('name')}"
            if place.get('rating') and place['rating'] != 'N/A':
                places_text += f" (Rating: {place['rating']}⭐)"
            places_text += f" - {place.get('address')}\n"
        
        prompt = f"""
        You are TravelMate, a friendly AI travel assistant. Create a natural response for the user.
        
        User asked: "{user_message}"
        
        Here are the places found:
        {places_text}
        
        Create a short, friendly response (2-3 sentences) that:
        1. Acknowledges what they're looking for
        2. Mentions the best option from the list
        3. Asks if they want more details
        
        Be conversational and use emojis occasionally.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini enhance error: {e}")
            return None
