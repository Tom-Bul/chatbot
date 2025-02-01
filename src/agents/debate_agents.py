import ollama
import random
from colorama import Fore, Style
from src.config import system_messages as msgs
from src.search.query import QueryGenerator
from src.search.search_engine import SearchEngine
from src.search.scraper import WebScraper
from src.utils.thinking_indicator import ThinkingIndicator
from src.utils.colors import Colors

class DebateController:
    def __init__(self):
        self.query_generator = QueryGenerator()
        self.search_engine = SearchEngine()
        self.scraper = WebScraper()
        self.name_prefixes = [
            "Logic", "Reason", "Wisdom", "Truth", "Think", "Mind",
            "Brain", "Intel", "Smart", "Sage", "Know", "Bright"
        ]
        self.name_suffixes = [
            "Master", "Seeker", "Finder", "Walker", "Weaver", "Smith",
            "Knight", "Sage", "Scholar", "Expert", "Guide", "Oracle"
        ]

    def _generate_agent_name(self):
        prefix = random.choice(self.name_prefixes)
        suffix = random.choice(self.name_suffixes)
        return f"{prefix}{suffix}"

    def run_debate(self, convo, fast_mode=False):
        # Skip debate if the last message is too short or just a greeting
        last_message = convo[-1]['content']
        if len(last_message.split()) < 30:
            return convo
        
        Colors.print("Starting debate", Colors.SYSTEM)
        print(f'{Fore.CYAN}[Starting debate]{" "*25}{Style.RESET_ALL}')
        
        # Get the topic and make it more debatable
        topic = convo[-1]['content']
        debate_context = (
            f"DEBATE TOPIC: The implications and impacts of these current events:\n{topic}\n\n"
            "Consider:\n"
            "- The societal implications\n"
            "- The policy implications\n"
            "- The potential consequences\n"
            "- Different stakeholder perspectives\n"
            "You MUST take a position on how these events should be interpreted and what they mean for society."
        )
        
        model = 'llama3.2:3b' if fast_mode else 'deepseek-r1:7b'
        
        # First Agent - Light blue
        first_color = Fore.LIGHTBLUE_EX
        first_name = self._generate_agent_name()
        Colors.print(f"{first_name} (First Agent)", Colors.FIRST_AGENT)
        
        research_context = self._get_research_context(topic, "research needed to support arguments about this topic")
        first_context = f"{debate_context}\n\nRESEARCH CONTEXT:\n{research_context}" if research_context else debate_context
        
        first_response = self._get_agent_response(
            msgs.first_debate_agent_msg,
            [{'role': 'user', 'content': first_context}],
            model,
            first_color
        )
        if first_response:
            convo.append({'role': 'assistant', 'content': first_response})
            print('\n')
            
            # Second Agent with research capability
            print(f'{Fore.CYAN}[Second Agent]{" "*26}{Style.RESET_ALL}')
            counter_research = self._get_research_context(topic, "research needed to counter these arguments")
            second_context = (
                f"FIRST POSITION ON THE IMPLICATIONS OF:\n{topic}\n\n"
                f"THEIR ARGUMENT:\n{first_response}\n\n"
                f"RESEARCH CONTEXT:\n{counter_research}\n\n" if counter_research else ""
                "Present a counter-argument about the implications and impacts. "
                "You MUST take the opposite position on how these events should be interpreted."
            )
            second_response = self._get_agent_response(
                msgs.second_debate_agent_msg,
                [{'role': 'user', 'content': second_context}],
                model,
                Fore.LIGHTGREEN_EX
            )
            if second_response:
                convo.append({'role': 'assistant', 'content': second_response})
                print('\n')
                
                # Third Party Analysis - gets both responses
                print(f'{Fore.CYAN}[Third Party Analysis]{" "*20}{Style.RESET_ALL}')
                analysis_context = (
                    f"TOPIC: {topic}\n\n"
                    f"FIRST POSITION:\n{first_response}\n\n"
                    f"SECOND POSITION:\n{second_response}\n\n"
                    "Analyze these opposing viewpoints."
                )
                analysis = self._get_agent_response(
                    msgs.third_party_analyzer_msg,
                    [{'role': 'user', 'content': analysis_context}],
                    model,
                    Fore.LIGHTMAGENTA_EX
                )
                if analysis:
                    convo.append({'role': 'assistant', 'content': analysis})
                    print('\n')
                    
                    # Add fun summary
                    print(f'{Fore.CYAN}[Quick Summary]{" "*20}{Style.RESET_ALL}')
                    summary = self._get_agent_response(
                        msgs.summary_agent_msg,
                        [{'role': 'user', 'content': analysis}],
                        'llama3.2:3b',
                        Fore.CYAN
                    )
                    if summary:
                        convo.append({'role': 'assistant', 'content': summary})
                        print('\n')
        
        return convo
        
    def _get_agent_response(self, system_msg, context, model='llama3.2:3b', color=Fore.YELLOW):
        try:
            response_stream = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_msg},
                    *context
                ],
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

    def _get_research_context(self, topic, research_purpose):
        print(f'{Fore.CYAN}[Searching for debate context]{" "*5}{Style.RESET_ALL}')
        try:
            # Extract actual text content, removing any <think> tags and their content
            clean_topic = ' '.join([
                line for line in topic.split('\n') 
                if not line.strip().startswith('<think>') and 
                not line.strip().startswith('</think>')
            ])
            
            # Use the query generator instead of custom logic
            query = self.query_generator.generate([{'role': 'user', 'content': clean_topic}])
            print(f'{Fore.GREEN}[Research query: {query}]{Style.RESET_ALL}')
            
            # Search
            results = self.search_engine.search(query)
            if not results:
                print(f'{Fore.YELLOW}[No search results found, using base context]{Style.RESET_ALL}')
                return (
                    "Consider discussing these aspects:\n"
                    "- Current political landscape\n"
                    "- Recent policy developments\n"
                    "- Public opinion and reactions\n"
                    "- Potential future implications"
                )
                
            for result in results:
                content = self.scraper.scrape(result['link'])
                if content and len(content.strip()) > 200:
                    print(f'{Fore.GREEN}[Found relevant content]{Style.RESET_ALL}')
                    return content[:2000]  # Limit content length
            
            print(f'{Fore.YELLOW}[No useful content found, using base context]{Style.RESET_ALL}')
            return "Consider discussing current events and their implications based on available information."
            
        except Exception as e:
            print(f'{Fore.RED}[Research error: {str(e)}]{Style.RESET_ALL}')
            return None 