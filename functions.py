import json
import os
import openai

def create_assistant(client):
    assistant_file_path = 'assistant.json'

    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else:
        # Create a new assistant with instructions
        assistant = client.beta.assistants.create(
            instructions="""
                Ping Identity AI Support Assistant for form builder, has been programmed to provide potential user with creating custom forms.
            """,
            model="gpt-4o-mini",  # Make sure to adjust the model version accordingly
            tools=[{
                "type": "file_search"  # Updated to a supported tool type
            }]
        )

        # Save the assistant's ID for future reference
        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant.id

    return assistant_id
