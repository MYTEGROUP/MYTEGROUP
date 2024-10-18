import openai
import os
from dotenv import load_dotenv
import logging
import time
from openai.error import RateLimitError, OpenAIError

# Load environment variables
load_dotenv()

# Retrieve OpenAI API key from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI with API key
openai.api_key = OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)

def generate_text(system_message, assistant_message, user_prompt, task_type='general', max_retries=3):
    """
    Generate text using OpenAI API with custom system, assistant, and prompt messages.
    Supports different task types like summarization and fact-checking.
    Implements retry logic for rate limits.

    Parameters:
    system_message (str): The system message guiding the assistant's behavior.
    assistant_message (str): The initial message to simulate the assistant's behavior.
    user_prompt (str): The user's input for generating a response.
    task_type (str): The type of task ('general', 'summarization', 'fact-checking').
    max_retries (int): Maximum number of retries for rate limit errors.

    Returns:
    dict: A dictionary with 'status' and 'response' keys.
    """
    # Adjust system_message based on task_type
    if task_type == 'summarization':
        system_message = "You are an AI assistant specialized in summarizing documents."
    elif task_type == 'fact-checking':
        system_message = "You are an AI assistant specialized in fact-checking claims."
    else:
        system_message = system_message  # Use default system message

    attempt = 0
    while attempt < max_retries:
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "assistant", "content": assistant_message},
                    {"role": "user", "content": user_prompt}
                ]
            )
            ai_response = response.choices[0].message.content
            # Return response in a structured format for backend compatibility
            return {"status": "success", "response": ai_response}

        except RateLimitError:
            logging.warning("Rate limit exceeded. Retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
            attempt += 1
        except OpenAIError as e:
            logging.error(f"OpenAI API error: {e}")
            return {"status": "error", "response": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error generating text: {e}")
            return {"status": "error", "response": str(e)}

    logging.error("Max retries exceeded due to rate limits.")
    return {"status": "error", "response": "Rate limit exceeded. Please try again later."}

# End of openaiservice.py