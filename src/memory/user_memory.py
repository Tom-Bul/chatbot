import json
import os
import ollama
from datetime import datetime
from colorama import Fore, Style
from src.config import system_messages as msgs
from src.utils.thinking_indicator import ThinkingIndicator

class UserMemory:
    def __init__(self):
        # Create memory directory if it doesn't exist
        self.memory_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'memory')
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Set memory file path
        self.memory_file = os.path.join(self.memory_dir, 'user_memory.json')
        self.memory = self._load_memory()

    def _load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
                
            empty_memory = self._get_empty_memory()
            with open(self.memory_file, 'w') as f:
                json.dump(empty_memory, f, indent=4)
            return empty_memory
            
        except Exception as e:
            print(f'{Fore.RED}[Error loading memory: {str(e)}]{Style.RESET_ALL}')
            return self._get_empty_memory()

    def _save_memory(self):
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=4)
        except Exception as e:
            print(f'{Fore.RED}[Error saving memory: {str(e)}]{Style.RESET_ALL}')

    def update_memory(self, message_content):
        print(f'{Fore.CYAN}[Analyzing memory]{" "*5}{Style.RESET_ALL}')
        response = self._analyze_for_memory(message_content)
        if response:
            self._update_from_analysis(response)
            self._save_memory()

    def _get_empty_memory(self):
        return {
            "personal_info": {},
            "interests": [],
            "preferences": {},
            "last_updated": None
        }

    def _analyze_for_memory(self, content):
        try:
            thinking = ThinkingIndicator()
            thinking.start("Analyzing message")
            
            current_memory = json.dumps(self.memory, indent=2)
            messages = [
                {'role': 'system', 'content': msgs.MEMORY_ANALYZER_PROMPT},
                {'role': 'user', 'content': (
                    f"Previous memory:\n{current_memory}\n\n"
                    f"New message from user:\n{content}\n\n"
                    "Extract any new personal information, interests, or preferences. "
                    "Return ONLY a JSON object with new information."
                )}
            ]
            response = ollama.chat(
                model='llama3.2:3b',
                messages=messages
            )
            
            thinking.stop()
            return response['message']['content']
            
        except Exception as e:
            thinking.stop()
            print(f'{Fore.RED}[Memory analysis error: {str(e)}]{Style.RESET_ALL}')
            return None

    def _cleanup_memory(self):
        """Remove empty, invalid, or nonsense entries from memory"""
        # Clean personal_info
        self.memory['personal_info'] = {
            k: v for k, v in self.memory['personal_info'].items() 
            if v and isinstance(v, str) and v.strip() and v.lower() not in ['null', 'none', 'unknown', '']
        }
        
        # Clean interests
        valid_interests = []
        for interest in self.memory['interests']:
            if (interest and 
                isinstance(interest, str) and 
                interest.strip() and 
                interest.lower() not in ['null', 'none', 'unknown', '', 'me', 'about', 'about you']):
                valid_interests.append(interest.lower().strip())
        self.memory['interests'] = list(dict.fromkeys(valid_interests))  # Remove duplicates while preserving order
        
        # Clean preferences
        self.memory['preferences'] = {
            k: v for k, v in self.memory['preferences'].items() 
            if v and isinstance(v, str) and v.strip() and v.lower() not in ['null', 'none', 'unknown', '', 'yes', 'no']
        }

    def _update_from_analysis(self, analysis):
        try:
            # First try to clean up the JSON
            analysis = analysis.strip()
            if not analysis.startswith('{'):
                analysis = '{'
            if not analysis.endswith('}'):
                analysis = analysis + '}'
            
            updates = json.loads(analysis)
            
            # Only update personal_info if there's new non-empty data
            if 'personal_info' in updates and updates['personal_info']:
                for key, value in updates['personal_info'].items():
                    if value:  # Only update if new value is not empty
                        self.memory['personal_info'][key] = value
                
            # Only update interests if there are new non-empty ones
            if 'interests' in updates and updates['interests']:
                new_interests = [i.lower() for i in updates['interests'] if i]  # Skip empty interests
                if new_interests:  # Only extend if there are valid interests
                    self.memory['interests'].extend(new_interests)
                    self.memory['interests'] = list(set(self.memory['interests']))  # Remove duplicates
                
            # Only update preferences if there are new non-empty ones
            if 'preferences' in updates and updates['preferences']:
                for key, value in updates['preferences'].items():
                    if value:  # Only update if new value is not empty
                        self.memory['preferences'][key] = value
            
            self.memory['last_updated'] = datetime.now().isoformat()
            self._cleanup_memory()  # Clean up after updates
            self._save_memory()
            
        except json.JSONDecodeError as e:
            print(f'{Fore.RED}[Memory update skipped: Invalid JSON format]{Style.RESET_ALL}')
        except Exception as e:
            print(f'{Fore.RED}[Memory update error: {str(e)}]{Style.RESET_ALL}')

    def get_relevant_memory(self, context):
        print(f'{Fore.CYAN}[Retrieving memory]{" "*5}{Style.RESET_ALL}')
        if not self.memory['personal_info'] and not self.memory['interests'] and not self.memory['preferences']:
            print(f'{Fore.YELLOW}[No stored memory]{Style.RESET_ALL}')
            return None
        
        return {
            'personal_info': self.memory['personal_info'],
            'interests': self.memory['interests'],
            'preferences': self.memory['preferences']
        } 