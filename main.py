import os
import json
from quart import Quart, request, jsonify
import openai
from dotenv import load_dotenv
from openai import AsyncOpenAI
import re
from quart_cors import cors
import uuid

load_dotenv()

# Initialize OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("Error: OPENAI_API_KEY not found in environment variables.")
print(f"API Key Loaded: {OPENAI_API_KEY}")  # Debugging line

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Quart app initialization
app = Quart(__name__)

# Model to use for form generation
app = cors(app, allow_origin="*")
MODEL = 'gpt-4o-mini'

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

        json_schema = {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
                "form": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string"
                        },
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string"
                                    },
                                    "label": {
                                        "type": "string"
                                    },
                                    "type": {
                                        "type": "string",
                                        "enum": ["text", "email", "password", "checkbox", "radio", "select", "submit"]
                                    },
                                    "placeholder": {
                                        "type": "string"
                                    },
                                    "required": {
                                        "type": "boolean"
                                    },
                                    "choices": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        },
                                        "minItems": 1
                                    }
                                },
                                "required": ["id", "label", "type", "required"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["fields", "title"]
                }
            },
            "required": ["form"]
        }

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={
                "type": "json_object"
            }
        )

        # Correct way to access the response content
        print (f"the uuid: {uuid.uuid1()}") 
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
        response_text = response_text.strip()

        if not response_text:
            raise ValueError("Received an empty response")

        # Debug: Log the response content to check if it's properly formatted
        print(f"Raw OpenAI Response: {response_text}")

        # Since the response is already in JSON format, parse it directly
        form_data = json.loads(response_text)

        add_uuid_to_form_fields(form_data)
        add_events_to_form_fields(form_data)

        return form_data

    except json.JSONDecodeError as e:
        print(f"Error parsing response as JSON: {e}")
        return {"error": "Failed to parse the form response"}
    except ValueError as e:
        print(f"Error extracting JSON: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred"}

def add_uuid_to_form_fields(form_data):
    print("form_data.get('fields', [])", form_data["form"].get('fields', []))
    print("form_data",form_data["form"]["fields"])
    for field in form_data["form"].get('fields', []):
        field['_id'] = str(uuid.uuid4())
    
    # If submit button exists, also generate a UUID for it
    # if "submitButton" in form_data:
    #     form_data["submitButton"]["_id"] = str(uuid.uuid4())

    # Debugging: Log the form data after UUIDs have been added
    print(f"Form data after adding UUIDs: {json.dumps(form_data, indent=2)}")

# def add_uuid_to_form_fields(form_data):
#     print(f"Adding UUIDs to form fields...{form_data}")

#     # Loop through each field and add a UUID
#     for field in form_data.get('fields', []):
#         print(f"Processing field: {field}")  # Debug log
#         if isinstance(field, dict) and 'name' in field:
#             field['_id'] = str(uuid.uuid4())  # Convert UUID to string
#             print(f"Added _id to field: {field['name']} -> {field['_id']}")  # Debug log
#         else:
#             print(f"Skipping invalid field: {field}")  # Debug log

#     # If submit button exists, also generate a UUID for it
#     if "submitButton" in form_data:
#         form_data["submitButton"]["_id"] = str(uuid.uuid4())
#         print(f"Added _id to submitButton -> {form_data['submitButton']['_id']}")  # Debug log

#     # Debugging: Log the form data after UUIDs have been added
#     print(f"Form data after adding UUIDs: {json.dumps(form_data, indent=2)}")


def add_events_to_form_fields(form_data):
    """
    Adds events like onFocus, onChange, onSubmit to form fields.
    Modifies the event handlers based on the type of field.
    """
    # Loop through each field and add events
    for field in form_data.get('fields', []):
        events = {}

        if field.get("type") == "text" or field.get("type") == "email" or field.get("type") == "password":
            # For text fields, we can add onFocus and onChange
            events["onFocus"] = "console.log('Field focused')"
            events["onChange"] = "console.log('Field value changed')"
        elif field.get("type") == "checkbox":
            # For checkboxes, we can add onChange
            events["onChange"] = "console.log('Checkbox value changed')"
        elif field.get("type") == "submit":
            # For the submit button, we add onClick
            events["onClick"] = "console.log('Form submitted')"
        
        field['events'] = events

    # Adding event to the submit button (if any)
    if "submitButton" in form_data:
        form_data["submitButton"]["events"] = {
            "onClick": "console.log('Submit button clicked')"
        }

# Run Quart app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
