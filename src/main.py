import ollama
import json
from colorama import Fore, Style
from src.agents.debate_agents import DebateController
from src.agents.opinion_agent import OpinionChecker
from src.search.query import QueryGenerator
from src.search.scraper import WebScraper
from src.search.search_engine import SearchEngine
from src.config import system_messages as msgs
from src.memory.user_memory import UserMemory
from src.utils.thinking_indicator import ThinkingIndicator, thinking_context
from src.utils.colors import Colors
from src.utils.model_manager import ModelManager  # New import for centralized chat calls

class Assistant:
    def __init__(self):
        self.debate_controller = DebateController()
        self.opinion_checker = OpinionChecker()
        self.query_generator = QueryGenerator()
        self.scraper = WebScraper()
        self.search_engine = SearchEngine()
        self.memory = UserMemory()
        self.fast_mode = False
        self.conversation = [msgs.assistant_msg]

    def run(self):
        while True:
            try:
                prompt = input('User: \n')
                self.conversation = self.process_input(prompt)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                Colors.print(f"Error: {str(e)}", Colors.ERROR)
                continue

    def process_input(self, prompt):
        # Check for fast mode and update accordingly
        if prompt.strip().endswith('-fast'):
            self.fast_mode = True
            prompt = prompt[:-5].strip()
            print(f'{Fore.CYAN}[Fast mode enabled]{" " * 5}{Style.RESET_ALL}')
        else:
            self.fast_mode = False

        # Update memory with user input
        self.memory.update_memory(prompt)
        
        # Append memory context if available, else add the user prompt directly
        memory_context = self.memory.get_relevant_memory(prompt)
        if memory_context:
            memory_prompt = (
                f"USER MEMORY CONTEXT:\n{json.dumps(memory_context, indent=2)}\n\n"
                f"USER PROMPT: {prompt}"
            )
            self.conversation.append({'role': 'user', 'content': memory_prompt})
        else:
            self.conversation.append({'role': 'user', 'content': prompt})

        # Check if search is needed using a context manager for the spinner
        if self._should_search(self.conversation[-1]):
            context = self._perform_search(self.conversation)
            self.conversation = self.conversation[:-1]
            
            if context:
                prompt = f'SEARCH RESULT: {context} \n\nUSER PROMPT: {prompt}'
            else:
                prompt = self._get_failed_search_prompt(prompt)
            
            self.conversation.append({'role': 'user', 'content': prompt})

        # Get assistant response using the centralized ModelManager.chat
        print(f'{Fore.CYAN}[Assistant responding]{" "*5}{Style.RESET_ALL}')
        model = ModelManager.get_model(self.fast_mode)
        response_stream = ModelManager.chat(
            messages=self.conversation,
            model=model,
            stream=True
        )
        if response_stream is None:
            Colors.print("Failed to get response from model", Colors.ERROR)
            return self.conversation

        complete_response = ''
        try:
            for chunk in response_stream:
                if chunk and 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    print(f'{Fore.YELLOW}{content}{Style.RESET_ALL}', end='', flush=True)
                    complete_response += content
        except Exception as e:
            Colors.print(f"Error processing response stream: {str(e)}", Colors.ERROR)
            return self.conversation
        
        self.conversation.append({'role': 'assistant', 'content': complete_response})
        print('\n')

        if self.opinion_checker.check(self.conversation):
            self.conversation = self.debate_controller.run_debate(self.conversation, self.fast_mode)
        
        return self.conversation

    def _should_search(self, message):
        # Use thinking_context to automatically start/stop the indicator
        try:
            with thinking_context("Checking if search needed"):
                response = ModelManager.chat(
                    messages=[
                        {'role': 'system', 'content': msgs.search_or_not_msg},
                        message
                    ],
                    model='llama3.2:3b'
                )
            content = response['message']['content']
            Colors.print(f"Search needed: {content}", Colors.SUCCESS)
            return 'true' in content.lower()
        except Exception as e:
            Colors.print(f"Error checking search need: {str(e)}", Colors.ERROR)
            return False

    def _perform_search(self, convo):
        print(f'{Fore.CYAN}[Starting search process]{" "*5}{Style.RESET_ALL}')
        query = self.query_generator.generate(convo)
        print(f'{Fore.GREEN}[Query: {query}]{Style.RESET_ALL}')
        
        results = self.search_engine.search(query)
        
        if not results:
            print(f'{Fore.RED}[Error: No search results found]{Style.RESET_ALL}')
            return None
        
        context = None
        context_found = False
        
        while not context_found and len(results) > 0:
            best_result = self._get_best_result(results, query, convo)
            if best_result is None:
                print(f'{Fore.RED}[Error: Failed to select best result]{Style.RESET_ALL}')
                return None
            
            try:
                page_link = results[best_result]['link']
                print(f'{Fore.CYAN}[Selected URL: {page_link}]{Style.RESET_ALL}')
                page_text = self.scraper.scrape(page_link)
                
                if page_text and self._validate_content(page_text, query, convo):
                    context = page_text
                    context_found = True
                    print(f'{Fore.GREEN}[Success: Got valid content]{Style.RESET_ALL}')
                else:
                    results.pop(best_result)
                    print(f'{Fore.RED}[Content not useful, trying next result]{Style.RESET_ALL}')
            except Exception as e:
                print(f'{Fore.RED}[Error processing result: {str(e)}]{Style.RESET_ALL}')
                results.pop(best_result)
                continue
        
        return context

    def _validate_content(self, content, query, convo):
        print(f'{Fore.CYAN}[Validating content]{" "*5}{Style.RESET_ALL}')
        if len(content) < 200:  # Basic length check
            return False
        
        needed_prompt = f'PAGE_TEXT: {content[:5000]} \nUSER_PROMPT: {convo[-1]["content"]} \nSEARCH_QUERY: {query}'
        try:
            response = ModelManager.chat(
                messages=[
                    {'role': 'system', 'content': msgs.contains_data_msg},
                    {'role': 'user', 'content': needed_prompt}
                ],
                model='llama3.2:3b',
                timeout=15
            )
            result = 'true' in response['message']['content'].lower()
            print(f'{Fore.GREEN}[Content validation: {result}]{Style.RESET_ALL}')
            return result
        except Exception as e:
            print(f'{Fore.RED}[Validation timeout/error - skipping]{Style.RESET_ALL}')
            return False

    def _get_best_result(self, results, query, convo):
        # Use thinking_context to wrap the selection process
        with thinking_context("Selecting best result"):
            best_msg = f'SEARCH_RESULTS: {results} \nUSER PROMPT: {convo[-1]["content"]} \nSEARCH_QUERY: {query}'
            for attempt in range(2):
                try:
                    response = ModelManager.chat(
                        messages=[
                            {'role': 'system', 'content': msgs.best_search_msg},
                            {'role': 'user', 'content': best_msg}
                        ],
                        model='llama3.2:3b'
                    )
                    result = response['message']['content'].strip()
                    if result.isdigit() and 0 <= int(result) < len(results):
                        print(f'{Fore.GREEN}[Selected result {result}]{Style.RESET_ALL}')
                        return int(result)
                    else:
                        print(f'{Fore.RED}[Invalid result: not a valid index]{Style.RESET_ALL}')
                except Exception as e:
                    print(f'{Fore.RED}[Error: invalid response format]{Style.RESET_ALL}')
                    continue
        print(f'{Fore.RED}[Failed to select result]{Style.RESET_ALL}')
        return None

    def _get_failed_search_prompt(self, original_prompt):
        return (
            f'USER PROMPT: \n{original_prompt} \n\nFAILED SEARCH: \nThe '
            'AI search model was unable to extract any reliable data. Explain that '
            'and ask if the user would like to search again or respond '
            'without web search context.'
        )

    def _get_agent_response(self, system_msg, context, model='deepseek-r1:7b', color=Fore.YELLOW):
        # Use thinking_context to ensure the indicator stops even on errors
        try:
            with thinking_context("Processing response"):
                response_stream = ModelManager.chat(
                    messages=[
                        {'role': 'system', 'content': system_msg},
                        *context
                    ],
                    model=model,
                    stream=True
                )
            complete_response = ''
            for chunk in response_stream:
                print(f'{color}{chunk["message"]["content"]}{Style.RESET_ALL}', end='', flush=True)
                complete_response += chunk["message"]["content"]
            
            return complete_response
            
        except Exception as e:
            print(f'{Fore.RED}[Error: {str(e)}]{Style.RESET_ALL}')
            return None

if __name__ == '__main__':
    assistant = Assistant()
    assistant.run() 