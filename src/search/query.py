import ollama
from datetime import datetime
from src.config import system_messages as msgs
from src.utils.logging import log_step
from colorama import Fore, Style

class QueryGenerator:
    def __init__(self, model='llama3.2:3b'):
        self.model = model
        self.time_qualifiers = [
            'latest', 'recent', 'current', 
            'last 24 hours', 'last week', 'this month'
        ]

    @log_step("Generating search query")
    def generate(self, convo):
        query_msg = (
            'CREATE A SEARCH QUERY FOR THIS PROMPT. '
            'Make it specific and include time frame and topic areas. '
            'For general news, specify major categories (politics, world events, technology, etc): \n'
            f'{convo[-1]["content"]}'
        )

        response = self._get_model_response(msgs.query_msg, query_msg)
        return self._clean_query(response)

    def _clean_query(self, query):
        # Remove any explanatory text after newlines
        query = query.split('\n')[0].strip()
        
        # Remove quotes and extra spaces
        query = ' '.join(query.replace('"', '').replace("'", '').split())
        
        # Remove year references
        query = ' '.join([word for word in query.split() 
                         if not word.isdigit() and not (word.startswith('20') and len(word) == 4)])
        
        # Ensure time qualifier
        if not any(qualifier in query.lower() for qualifier in self.time_qualifiers):
            query = f'latest {query}'
        
        # Limit length
        words = query.split()
        if len(words) > 8:
            query = ' '.join(words[:8])
        
        return query

    def _get_model_response(self, sys_msg, query_msg):
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': (
                        'You are a search query generator. Generate ONLY the query text, no explanations or notes.\n'
                        'Rules:\n'
                        '1. Keep queries short and focused\n'
                        '2. Include time qualifiers (latest, recent, etc.)\n'
                        '3. No quotes or formatting\n'
                        '4. No commentary or explanations\n'
                        '5. Maximum 6-8 words'
                    )},
                    {'role': 'user', 'content': query_msg}
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f'{Fore.RED}[Query generation error: {str(e)}]{Style.RESET_ALL}')
            return 'latest news' 