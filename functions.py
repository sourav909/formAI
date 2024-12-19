import openai
import os
import json
from openai import AsyncOpenAI

# Initialize the AsyncOpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_dynamic_form(user_input: str):
    """
    Use OpenAI's ChatCompletion API to generate a dynamic form based on user input.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4",  # Using GPT-4
            messages=[
                {"role": "system", "content": "You are an AI assistant that helps generate form structures."},
                {"role": "user", "content": f"Create a dynamic form based on this request: {user_input}"}
            ],
            temperature=0.7,
            max_tokens=500
        )

        # Extract and parse the response content
        assistant_response = response['choices'][0]['message']['content']
        form_json = parse_form_json(assistant_response)

        return form_json

    except Exception as e:
        print(f"Error generating dynamic form: {e}")
        return {"error": "Failed to generate form"}

def parse_form_json(response_text):
    """
    Convert the assistant's response into a structured JSON format.
    """
    form_json = {
        "fields": [],
        "submit_button": {
            "action": "submit",
            "label": "Submit",
            "type": "button"
        }
    }

    try:
        form_data = json.loads(response_text)
        if "fields" in form_data:
            form_json["fields"] = form_data["fields"]
        if "submit_button" in form_data:
            form_json["submit_button"] = form_data["submit_button"]
    except json.JSONDecodeError:
        print("Error parsing the response as JSON.")
        form_json = {"error": "Failed to parse the form response"}

    return form_json
