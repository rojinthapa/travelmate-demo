import re

class NLPProcessor:
    def __init__(self):
        self.user_location = None
    
    def set_current_location(self, location):
        self.user_location = location
    
    def process_message(self, message, user_location=None):
        message_lower = message.lower()
        
        # Greetings
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'greetings', 'good morning']):
            return 'greeting', {}
        
        # Help
        if any(word in message_lower for word in ['help', 'what can you do', 'assist']):
            return 'help', {}
        
        # Find places
        if any(word in message_lower for word in ['find', 'search', 'where', 'show', 'look for']):
            place_type = 'restaurant'
            if any(word in message_lower for word in ['hotel', 'stay', 'accommodation', 'lodging']):
                place_type = 'hotel'
            elif any(word in message_lower for word in ['attraction', 'tourist', 'sight', 'landmark', 'museum']):
                place_type = 'attraction'
            
            # Extract location
            cities = ['paris', 'london', 'tokyo', 'new york', 'bali', 'sydney', 'rome', 'dubai', 
                      'amsterdam', 'barcelona', 'berlin', 'prague', 'venice']
            location = None
            
            for city in cities:
                if city in message_lower:
                    location = city.title()
                    break
            
            # Check for "near me"
            if not location and ('near me' in message_lower or 'nearby' in message_lower):
                if self.user_location:
                    location = self.user_location
                else:
                    location = "your current location"
            
            # Extract from patterns like "in Paris"
            if not location:
                match = re.search(r'in\s+([A-Za-z\s]+)', message)
                if match:
                    location = match.group(1).strip().title()
            
            entities = {'place_type': place_type, 'location': location}
            return 'find_places', entities
        
        # Unknown
        return 'unknown', {}
