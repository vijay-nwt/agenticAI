import json
from users.models import Record  
import autogen
from django.conf import settings  # Import settings

# OpenAI API Configuration
config_list = [
    {"model": "gpt-4o-mini", "api_key": settings.OPENAI_API_KEY}
]

# Define the AI Assistant Agent
assistant = autogen.AssistantAgent(
    name="CRUD_Agent",
    system_message="You are an AI assistant that translates user prompts into CRUD operations. "
               "Ensure your response is always in valid JSON format with keys: "
               "'action', 'name', 'age', 'address', 'department', 'id' (if applicable). "
               "For a 'read' operation, if the user asks for all records, return {'action': 'read', 'all': true}. "
               "If a name or ID is given, include {'action': 'read', 'name': 'X'} or {'action': 'read', 'id': X}. "
               "If the request is not a CRUD operation, respond with {'error': 'Invalid request'}.",
    llm_config={"config_list": config_list},
)

# Function to process AI responses and perform CRUD operations
def execute_crud(prompt):
    print("Prompt:", prompt)

    # Generate AI response directly without UserProxyAgent
    response = assistant.generate_reply(messages=[{"role": "user", "content": prompt}])

    print("response:", response)  # 🔍 Debugging line
    
   
    if isinstance(response, str):  # Ensure response is not mistakenly a raw string
        raw_response = response
    elif isinstance(response, dict) and "content" in response:
        raw_response = response["content"]
    else:
        return {"error": "Unexpected AI response format."}


    

    # Convert AI response to JSON
    try:
        operation = json.loads(raw_response)
        print("Parsed Operation:", operation)

        action = operation.get("action", "").lower()

        if action == "create":
            item = Record.objects.create(
                name=operation["name"],
                age=operation["age"],
                address=operation["address"],
                department=operation["department"]
            )
            return {"message": f"Item '{item.name}' created successfully!", "id": item.id}

        elif action == "read":
            # Check if "name" is provided
            if "name" in operation:
                items = list(Record.objects.filter(name=operation["name"]).values("id", "name", "age", "address", "department"))
                if items:
                    return {"message": f"Records found: {items}"}  # Return all matches
                return {"message": f"No records found for name: {operation['name']}"}
            
            # Check if "id" is provided
            elif "id" in operation:
                item = Record.objects.filter(id=operation["id"]).values("id", "name", "age", "address", "department").first()
                if item:
                    return {"message": f"Record found: {item}"}
                return {"message": f"No record found for ID: {operation['id']}"}
            
            # If neither name nor ID is provided, return all records
            else:
                items = list(Record.objects.all().values("id", "name", "age", "address", "department"))
                if items:
                    return {"message": f"All records: {items}"}
                return {"message": "No records found."}


        elif action == "update":
            # Check if name or id is provided for updating
            if "id" in operation:
                item = Record.objects.get(id=operation["id"])
            elif "name" in operation:
                item = Record.objects.get(name=operation["name"])
            else:
                return {"error": "Please provide either an id or a name for the update."}
                
            item.name = operation.get("name", item.name)
            item.age = operation.get("age", item.age)
            item.address = operation.get("address", item.address)
            item.department = operation.get("department", item.department)
            item.save()
            return {"message": f"Item '{item.id}' updated successfully!"}

        elif action == "delete":
            # Check if name or id is provided for deleting
            if "id" in operation:
                item = Record.objects.get(id=operation["id"])
            elif "name" in operation:
                item = Record.objects.get(name=operation["name"])
            else:
                return {"error": "Please provide either an id or a name for the deletion."}
                
            item.delete()
            return {"message": f"Item '{item.id}' deleted successfully!"}

        else:
            return {"error": "Invalid action received. Please ask for a CRUD operation only."}

    except json.JSONDecodeError:
        return response
    except Exception as e:
        return {"error": str(e)}


