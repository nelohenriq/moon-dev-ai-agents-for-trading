"""
🌙 Moon Dev's OpenAI Model Implementation
Built with love by Moon Dev 🚀
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class OpenAIModel(BaseModel):
    """Implementation for OpenAI's models"""
    
    AVAILABLE_MODELS = {
        "o1": {
            "description": "Latest O1 model with reasoning capabilities",
            "input_price": "$0.01/1K tokens",
            "output_price": "$0.03/1K tokens"
        },
        "o1-mini": {
            "description": "Smaller O1 model with reasoning capabilities",
            "input_price": "$0.005/1K tokens",
            "output_price": "$0.015/1K tokens"
        },
        "gpt-4-turbo-preview": "Most capable GPT-4 model",
        "gpt-4": "Standard GPT-4 model",
        "gpt-3.5-turbo": "Fast and efficient GPT-3.5"
    }
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo", **kwargs):
        self.model_name = model_name
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the OpenAI client"""
        try:
            self.client = OpenAI(api_key=self.api_key)
            cprint(f"✨ Initialized OpenAI model: {self.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize OpenAI model: {str(e)}", "red")
            self.client = None
    
    def generate_response(self, system_prompt, user_content, **kwargs):
        """Generate a response using the OpenAI model"""
        try:
            # Special handling for O1 models
            if self.model_name.startswith('o1'):
                # Remove unsupported parameters for O1
                if 'max_tokens' in kwargs:
                    kwargs['max_completion_tokens'] = kwargs.pop('max_tokens')
                if 'temperature' in kwargs:
                    kwargs.pop('temperature')
                
                # O1 models use user role for both messages
                messages = [
                    {
                        "role": "user",
                        "content": f"Instructions: {system_prompt}\n\nInput: {user_content}"
                    }
                ]
            else:
                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            
            # Create completion with appropriate parameters
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **kwargs
            )
            
            return response.choices[0].message

        except Exception as e:
            cprint(f"❌ OpenAI generation error: {str(e)}", "red")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "openai" 