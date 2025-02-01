import ollama
from src.utils.colors import Colors

class ModelManager:
    FAST_MODEL = 'llama3.2:3b'
    DEFAULT_MODEL = 'deepseek-r1:7b'
    
    @staticmethod
    def get_model(fast_mode=False):
        return ModelManager.FAST_MODEL if fast_mode else ModelManager.DEFAULT_MODEL
    
    @staticmethod
    def chat(messages, model=FAST_MODEL, stream=False, timeout=None):
        try:
            options = {}
            if timeout:
                options['timeout'] = timeout
            response = ollama.chat(
                model=model,
                messages=messages,
                stream=stream,
                options=options
            )
            if stream:
                return response  # Return the stream directly for the caller to process
            return response
        except Exception as e:
            Colors.print(f"Chat error: {str(e)}", Colors.ERROR)
            # Consider invoking a centralized error handler here
            return None 