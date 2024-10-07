import json
import subprocess
import os
from colorama import Back, init, Fore
from groq import Groq

def execute_kubectl_command(command):
    """
    Executes a kubectl command against the current Kubernetes cluster.
    Adds the 'kubectl' prefix if it's not already there.
    Deleting resources is disabled for safety.
    """
    if not command.startswith("kubectl"):
        command = f"kubectl {command}"

    if command.startswith("kubectl delete"):
        return "Deleting resources is disabled for safety reasons."

    try:
        output = subprocess.check_output(command, shell=True)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Error executing kubectl command: {e}"

# Initialize the Groq client with the API key from environment variables
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Define the model to be used
model_name = "llama3-8b-8192"

# Define the available tools (functions) that the model can use
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_kubectl_command",
            "description": "Executes the kubectl command against the current Kubernetes cluster",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The kubectl command to execute",
                    },
                },
                "required": ["command"],
            },
        },
    }
]

def get_chat_completion(user_input):
    """
    Generates a chat completion using the Groq model.
    Handles tool calls if the model requires them.
    """
    messages = [{"role": "user", "content": user_input}]
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
    except groq.BadRequestError as e:
        if 'tool_use_failed' in e.error['code']:
            # If the model tries to call a non-existent function, fall back to a default response
            return "I'm sorry, I didn't understand that. I can only execute kubectl commands."
        else:
            raise e

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    if tool_calls:
        available_functions = {
            "execute_kubectl_command": execute_kubectl_command,
        }
        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                command=function_args.get("command"),
            )
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )
        second_response = client.chat.completions.create(
            model=model_name,
            messages=messages,
        )
        return second_response.choices[0].message.content
    else:
        return response_message.content

def run_conversation():
    """
    Runs the conversation loop with the user.
    """
    print("Welcome to the Kubernetes Chatbot!")
    print("You can ask me anything about your Kubernetes cluster.")
    while True:
        print(Back.CYAN + Fore.BLACK + " User Input: ", end="")
        print(" > ", end="")
        user_input = input()
        if user_input.lower() == "exit" or user_input.lower() == "q":
            print("Goodbye!")
            break
        else:
            response = get_chat_completion(user_input)
            print("")
            print(Back.GREEN + Fore.BLACK + " Chatbot Response: ", end="")
            print(" > ", end="")
            print(f"{response}")
            print("")

def main():
    """
    Initializes the chatbot and starts the conversation loop.
    """
    init(autoreset=True)
    run_conversation()

if __name__ == "__main__":
    main()
