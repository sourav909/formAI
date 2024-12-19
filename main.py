from quart import Quart, request, jsonify
from quart_cors import cors  # Correct import for CORS handling
import openai
import os
import json
import uuid
from dotenv import load_dotenv
from openai import AsyncOpenAI
from jsonschema import validate, ValidationError

load_dotenv()

# Initialize OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("Error: OPENAI_API_KEY not found in environment variables.")
print(f"API Key Loaded: {OPENAI_API_KEY}")  # Debugging line

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Quart app initialization
app = Quart(__name__)

# Apply CORS to the app
app = cors(app, allow_origin="*")  # Correct usage of CORS with Quart

# Model to use for form generation
MODEL = 'gpt-4o-mini'

# Define the JSON schema that you want to validate against
json_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "form": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "_id": {"type": "string"},
                            "label": {"type": "string"},
                            "name": {"type": "string"},
                            "placeholder": {"type": "string"},
                            "required": {"type": "boolean"},
                            "type": {"type": "string", "enum": ["text", "email", "password", "checkbox", "radio", "select", "textarea", "tel", "date", "number"]},
                            "options": {"type": "array", "items": {"type": "string"}, "minItems": 1}
                        },
                        "required": ["_id", "label", "name", "type", "required"],
                        "additionalProperties": False
                    }
                },
                "submit_button": {
                    "type": "object",
                    "properties": {"label": {"type": "string"}, "onclick": {"type": "string"}},
                    "required": ["label", "onclick"]
                }
            },
            "required": ["title", "fields"],
            "additionalProperties": False
        }
    },
    "required": ["form"],
    "additionalProperties": False
}

# Define field mappings
field_mappings = {
    "form name": "title",
    "form title": "title",
    "form description": "description",
    "submit_button": "submit_button",  
    "firstname": "name",  
    "lastname": "name",
    "emailaddress": "email",  
    "user_email": "email",
    "phone": "tel",
    "textarea": "textarea",
}

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

        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"}
        )

        # Correct way to access the response content
        assistant_response = response.choices[0].message.content

        # Try to parse the OpenAI response into JSON
        form_json = parse_form_json(assistant_response)

        return jsonify({"form": form_json})

    except Exception as e:
        print(f"Error generating form: {e}")  # Debugging line
        return jsonify({"error": "Failed to generate form"}), 500

def parse_form_json(response_text):
    try:
        response_text = response_text.strip()

        if not response_text:
            raise ValueError("Received an empty response")

        # Debug: Log the response content to check if it's properly formatted
        print(f"Raw OpenAI Response: {response_text}")

        # Since the response is already in JSON format, parse it directly
        form_data = json.loads(response_text)

        # Create the output in your schema format
        form_json = {
            "form": {
                "title": form_data.get("form", {}).get("title", ""),
                "description": form_data.get("form", {}).get("description", ""),
                "fields": [],
                "submit_button": {
                    "label": form_data.get("form", {}).get("submit", {}).get("label", ""),
                    "onclick": form_data.get("form", {}).get("submit", {}).get("action", "")
                }
            }
        }

        # Map fields from the response to match the schema
        for field in form_data.get("form", {}).get("fields", []):
            field_data = {
                "_id": str(uuid.uuid4()),  
                "label": field.get("label", ""),
                "name": map_field_name(field.get("label", "")),  
                "type": field.get("type", ""),
                "required": field.get("required", False),
                "placeholder": field.get("placeholder", "")
            }
            form_json["form"]["fields"].append(field_data)

        # Validate the transformed form data against the schema
        validate(instance=form_json, schema=json_schema)

        add_uuid_to_form_fields(form_json)

        return form_json

    except json.JSONDecodeError as e:
        print(f"Error parsing response as JSON: {e}")
        return {"error": "Failed to parse the form response"}
    except ValueError as e:
        print(f"Error extracting JSON: {e}")
        return {"error": str(e)}
    except ValidationError as e:
        print(f"Validation Error: {e}")
        return {"error": "Form data does not conform to the schema"}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred"}

def map_field_name(field_name):
    return field_mappings.get(field_name.lower(), field_name)  # Return mapped name or original

def add_uuid_to_form_fields(form_data):
    for field in form_data["form"].get('fields', []):
        if '_id' not in field:
            field['_id'] = str(uuid.uuid4())

    print(f"Form data after adding UUIDs: {json.dumps(form_data, indent=2)}")


# Run Quart app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
