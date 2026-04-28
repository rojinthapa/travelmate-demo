import spacy
from spacy.matcher import Matcher
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import re

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    print("Downloading spaCy model...")
    import os
    os.system("python -m spacy download en_core_web_md")
    nlp = spacy.load("en_core_web_md")

class NLPProcessor:
    def __init__(self):
        # Initialize geocoder
        self.geocoder = Nominatim(user_agent="travelmate")
        
        # Define patterns for intent recognition
        self.matcher = Matcher(nlp.vocab)
        
        # Patterns for different intents
        patterns = {
            "greeting": [
                [{"LOWER": {"IN": ["hi", "hello", "hey", "greetings"]}}],
                [{"LOWER": "good"}, {"LOWER": {"IN": ["morning", "afternoon", "evening"]}}]
            ],
            "help": [
                [{"LOWER": "help"}],
                [{"LOWER": "what"}, {"LOWER": "can"}, {"LOWER": "you"}, {"LOWER": "do"}]
            ],
            "find_places": [
                [{"LOWER": "find"}, {"LOWER": {"IN": ["restaurants", "hotels", "attractions"]}}],
                [{"LOWER": "where"}, {"LOWER": "are"}, {"LOWER": {"IN": ["restaurants", "hotels", "attractions"]}}],
                [{"LOWER": "show"}, {"LOWER": "me"}, {"LOWER": {"IN": ["restaurants", "hotels", "attractions"]}}]
            ],
            "get_info": [
                [{"LOWER": "tell"}, {"LOWER": "me"}, {"LOWER": "about"}],
                [{"LOWER": "what"}, {"LOWER": "is"}],
                [{"LOWER": "how"}, {"LOWER": "do"}]
            ]
        }
        
        # Add patterns to matcher
        for intent, pattern_list in patterns.items():
            self.matcher.add(intent, pattern_list)
    
    def process_message(self, message, user_location=None):
        """
        Process user message to determine intent and extract entities
        """
        # Convert message to lowercase for easier matching
        message = message.lower()
        
        # Define place types and their keywords
        place_types = {
            'restaurant': ['restaurant', 'food', 'dining', 'cafe', 'café', 'bar', 'pub', 'eatery'],
            'hotel': ['hotel', 'accommodation', 'lodging', 'inn', 'resort', 'hostel'],
            'attraction': ['attraction', 'sight', 'landmark', 'museum', 'gallery', 'park', 'monument']
        }
        
        # Define location keywords
        location_keywords = ['in', 'at', 'near', 'around', 'by', 'close to']
        
        # Initialize entities
        entities = {
            'place_type': None,
            'location': None,
            'query': None
        }
        
        # Extract place type
        for place_type, keywords in place_types.items():
            if any(keyword in message for keyword in keywords):
                entities['place_type'] = place_type
                break
        
        # Extract location using spaCy
        doc = nlp(message)
        
        # Look for location entities
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:  # GPE for geopolitical entities, LOC for locations
                entities['location'] = ent.text
                break
        
        # If no location found, try to extract after location keywords
        if not entities['location']:
            for keyword in location_keywords:
                if keyword in message:
                    parts = message.split(keyword)
                    if len(parts) > 1:
                        potential_location = parts[1].strip()
                        # Clean up the location string
                        potential_location = re.sub(r'[.,!?]', '', potential_location)
                        if potential_location:
                            entities['location'] = potential_location
                            break
        
        # Extract query for information requests
        if any(word in message for word in ['tell me about', 'information', 'details', 'what is']):
            entities['query'] = self._extract_query(doc)
        
        # Determine intent based on keywords and structure
        if any(word in message for word in ['hi', 'hello', 'hey', 'greetings']):
            intent = 'greeting'
        elif any(word in message for word in ['help', 'assist', 'support']):
            intent = 'help'
        elif any(word in message for word in ['find', 'search', 'look for', 'where is', 'where are']):
            intent = 'find_places'
        else:
            intent = 'unknown'
        
        return intent, entities
    
    def _extract_location(self, doc):
        """
        Extract location from text using spaCy's NER and geocoding
        """
        # Look for location entities
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                try:
                    # Geocode the location to get coordinates
                    location = self.geocoder.geocode(ent.text)
                    if location:
                        return {
                            "name": ent.text,
                            "latitude": location.latitude,
                            "longitude": location.longitude
                        }
                except GeocoderTimedOut:
                    continue
        
        # If no location found in entities, try to find location indicators
        location_indicators = ["in", "at", "near", "around", "close to"]
        for i, token in enumerate(doc):
            if token.text in location_indicators and i + 1 < len(doc):
                location_text = doc[i+1:].text
                try:
                    location = self.geocoder.geocode(location_text)
                    if location:
                        return {
                            "name": location_text,
                            "latitude": location.latitude,
                            "longitude": location.longitude
                        }
                except GeocoderTimedOut:
                    continue
        
        return None
    
    def _extract_query(self, doc):
        """
        Extract the main query from information requests
        """
        # Remove common question words and verbs
        stop_words = {"what", "is", "are", "tell", "me", "about", "how", "do", "can", "you"}
        query_words = [token.text for token in doc if token.text not in stop_words]
        return " ".join(query_words) 

