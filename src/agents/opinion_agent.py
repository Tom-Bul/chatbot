import ollama
from src.utils.logging import log_step
from src.config import system_messages as msgs
from colorama import Fore, Style

class OpinionChecker:
    def __init__(self, model='llama3.2:3b'):
        self.model = model

    @log_step("Opinion check")
    def check(self, convo):
        # Skip checking greetings or very short responses
        last_response = convo[-1]['content']
        if len(last_response.split()) < 30 in last_response.lower():
            return False
            
        prompt = f'{convo[-1]}'
        response = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': msgs.opinion_check_agent_msg},
                {'role': 'user', 'content': prompt}
            ]
        )
        content = response['message']['content']
        print(f'{Fore.LIGHTRED_EX}IS OPINION BASED: {content}{Style.RESET_ALL}')
        return 'true' in content.lower() 