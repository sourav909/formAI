import os
import json
from quart import Quart, request, jsonify
import openai
from dotenv import load_dotenv
from openai import AsyncOpenAI
import re

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("Error: OPENAI_API_KEY not found in environment variables.")
print(f"API Key Loaded: {OPENAI_API_KEY}")  # Debugging line

# Initialize the AsyncOpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Quart app initialization
app = Quart(__name__)

# Model to use for form generation
MODEL = 'gpt-4'

@app.route('/generate-form', methods=['POST'])
async def generate_form():
    try:
        # Get user input from JSON body
        data = await request.json
        user_input = data.get('message', '')

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        print(f"User Input: {user_input}")  # Debugging line

        # Define OpenAI messages
        messages = [
            {"role": "system", "content": "You are an AI assistant that generates form JSON structures based on user requests."},
            {"role": "user", "content": f"Create a form for the following request: {user_input}"}
        ]

        # Get completion from OpenAI
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        # Correct way to access the response content
        print(f"OpenAI Response content: {response.choices[0].message.content}")
        assistant_response = response.choices[0].message.content

        # Try to parse the OpenAI response into JSON
        form_json = parse_form_json(assistant_response)

        return jsonify({"form": form_json})

    except Exception as e:
        print(f"Error generating form: {e}")  # Debugging line
        return jsonify({"error": "Failed to generate form"}), 500

def parse_form_json(response_text):
    """
    Extract and return only the JSON structure from the response.
    """
    try:
        # Extract the JSON part from the response text using regex
        json_part_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        if not json_part_match:
            raise ValueError("No valid JSON part found in response")

        # Extract the JSON content inside the code block
        json_part = json_part_match.group(1).strip()

        # Parse the extracted JSON part
        form_data = json.loads(json_part)

        return form_data

    except json.JSONDecodeError as e:
        print(f"Error parsing response as JSON: {e}")
        return {"error": "Failed to parse the form response"}
    except ValueError as e:
        print(f"Error extracting JSON: {e}")
        return {"error": str(e)}


# Run Quart app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
