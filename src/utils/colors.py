from colorama import Fore, Style

class Colors:
    # System colors
    SYSTEM = Fore.CYAN
    ERROR = Fore.RED
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    
    # Agent colors
    FIRST_AGENT = Fore.LIGHTBLUE_EX
    SECOND_AGENT = Fore.LIGHTGREEN_EX
    ANALYZER = Fore.LIGHTMAGENTA_EX
    SUMMARY = Fore.CYAN
    
    # Utility method
    @staticmethod
    def print(text, color=SYSTEM, end='\n'):
        print(f'{color}[{text}]{Style.RESET_ALL}', end=end, flush=True)
    
    @staticmethod
    def stream(text, color=SYSTEM):
        print(f'{color}{text}{Style.RESET_ALL}', end='', flush=True) 