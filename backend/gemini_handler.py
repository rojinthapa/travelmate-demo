import google.generativeai as genai
import os
import json

class GeminiHandler:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def process_message(self, user_message):
        prompt = f"""
        You are TravelMate, an AI travel assistant. Analyze this user message and return JSON:
        
        User: "{user_message}"
        
        Return ONLY this JSON format (no other text):
        {{
            "intent": "greeting|find_places|help|unknown",
            "place_type": "restaurant|hotel|attraction|null",
            "location": "city name or null",
            "budget": "budget|null", 
            "preferences": ["list", "of", "keywords"],
            "friendly_response": "short friendly reply to user"
        }}
        """
        
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
