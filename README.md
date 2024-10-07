# Chatbot to Interact with a Kubernetes Cluster

In today's fast-paced technological landscape, managing and interacting with complex systems like Kubernetes clusters can be a daunting task. This is where chatbots come into play. Chatbots are automated programs designed to simulate conversations with human users. They can be incredibly useful in various scenarios, including interacting with Kubernetes clusters. In this article, we will walk through the process of setting up a chatbot that interacts with a Kubernetes cluster using Minikube and Docker. We will also explain a Python script that leverages the Groq model to facilitate this interaction.

## Why Use a Chatbot for Kubernetes Cluster Interaction?

Managing a Kubernetes cluster involves numerous tasks, such as deploying applications, scaling resources, monitoring performance, and troubleshooting issues. While Kubernetes provides powerful command-line tools like `kubectl`, interacting with the cluster can still be complex and time-consuming. A chatbot can simplify this process by providing a user-friendly interface for executing commands and retrieving information.

## Environment Setup
This article describes building a minimal chatbot using:
 - `Minikube` as a Kubernetes environment. Minikube is a lightweight Kubernetes implementation that creates a VM on your local machine and deploys a simple cluster containing only one node. Kubernetes allows us to deploy, manage and scale docker images.
 - Minikube requires a container runtime to operate, and `Docker Desktop` provides a reliable and widely-supported container runtime. Using Docker Desktop with Minikube ensures compatibility, ease of use, and a consistent environment for local Kubernetes development and testing.
 - `Python` to implement the chatbot.

### Installing Minikube

Minikube is a tool that allows you to run a single-node Kubernetes cluster locally. Here’s how you can install it:
1. **Install Docker:**
Install Docker Desktop on your system. The easiest way to do so is to get the .dmg file from Docker’s website.
2. **Install Minikube:**
Install Minikube and kubectl (the command line tool to interact with Kubernetes) using Homebrew. Note that kubectl will show up as kubernetes-cli in the list of installed packages.
      ```sh
      $ brew install minikube kubectl
      ```

3. **Start Minikube:**
You need to open docker desktop and then run below command to start minikube on your terminal.
    ```sh
    $ minikube start
    ```
    You can check that everything has been installed properly by checking the version numbers of the various tools.
   ```sh
   $ docker --version
   $ minikube version
   $ kubectl version
   ```



### Setting Up the Python Environment for chatbot

Ensure you have Python installed on your system. Setting of python virtual environment to isolates project dependencies, ensuring that each project has its own set of libraries and avoiding conflicts between different projects. This promotes reproducibility, simplifies dependency management, and enhances project portability.You can install the necessary Python packages using pip.

   ```sh
   $ mkdir chatbot-k8s
   $ cd chatbot-k8s
   
   # Set up python venv
   $ python3 -m venv .venv
   $ source .venv/bin/activate
   $ pip install subprocess colorama groq
   
   # Create chat_with_k8s.py file and add code 
   $ touch chat_with_k8s.py
   ```

## Chatbot Script Explanation

The following Python script sets up a chatbot that can interact with a Kubernetes cluster using the Groq model.


### 1. Importing Necessary Libraries

```python
import json
import subprocess
import os
from colorama import Back, init, Fore
from groq import Groq
```

**Explanation**:
This block imports the necessary libraries for the chatbot to function. The `json` library is used for parsing JSON data, which is essential for handling function arguments and responses. The `subprocess` library is used to execute shell commands, specifically `kubectl` commands in this case. The `os` library is used to access environment variables, such as the API key for the Groq client. The `colorama` library is used to add color to terminal output, making the conversation more visually appealing. Finally, the `groq` library is the client library for interacting with the Groq API, which is used to generate chat completions.

### 2. Executing Kubectl Commands

```python
def execute_kubectl_command(command):
    """
    Executes a kubectl command against the current Kubernetes cluster.
    Adds the 'kubectl' prefix if it's not already there.
    Deleting resources is disabled for safety reasons.
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
```

**Explanation**:
This function, `execute_kubectl_command`, is responsible for executing `kubectl` commands against the current Kubernetes cluster. It first checks if the command starts with `kubectl` and adds the prefix if it's missing. For safety reasons, the function disables any `kubectl delete` commands to prevent accidental deletion of resources. The function then attempts to execute the command using the `subprocess` library. If the command executes successfully, the output is returned. If an error occurs, the function catches the exception and returns an error message.

### 3. Initializing the Groq Client

```python
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
```

**Explanation**:
This block initializes the Groq client using the API key from environment variables. The Groq client is used to interact with the Groq API for generating chat completions. By initializing the client with the API key, the chatbot can authenticate and make requests to the Groq API. This is a crucial step for enabling the chatbot to generate responses based on user input. You can generate API Key fro here(https://console.groq.com/docs/quickstart)

### 4. Defining the Model and Tools

```python
model_name = "llama3-8b-8192"

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
```

**Explanation**:
This block defines the model to be used (`llama3-8b-8192`) and the available tools (functions) that the model can use. The `tools` list includes a function for executing `kubectl` commands. Each tool is defined with a type, name, description, and parameters. The parameters specify the expected input for the function, in this case, a string representing the `kubectl` command to execute. This definition allows the model to call the `execute_kubectl_command` function when needed, enabling the chatbot to perform actions based on user input.

### 5. Generating Chat Completions

```python
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
```

**Explanation**:
This function, `get_chat_completion`, generates a chat completion using the Groq model. It takes user input as an argument and constructs a list of messages to send to the model. The function attempts to create a chat completion using the specified model, messages, tools, and tool choice. If the model tries to call a non-existent function, the function catches the `BadRequestError` and returns a default response. If the model requires tool calls, the function handles them by calling the appropriate functions and appending the responses to the messages. It then generates a second response if necessary. This function is the core of the chatbot's functionality, enabling it to generate responses based on user input and perform actions using the defined tools.

### 6. Running the Conversation Loop

```python
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
```

**Explanation**:
This function, `run_conversation`, runs the conversation loop with the user. It starts by welcoming the user and explaining that they can ask questions about their Kubernetes cluster. The function then enters a loop where it prompts the user for input. If the user types "exit" or "q", the loop breaks, and the chatbot says goodbye. Otherwise, the function calls `get_chat_completion` with the user input to generate a response. The chatbot's response is then displayed to the user. This loop continues until the user decides to exit the conversation.

### 7. Main Function

```python
def main():
    """
    Initializes the chatbot and starts the conversation loop.
    """
    init(autoreset=True)
    run_conversation()

if __name__ == "__main__":
    main()
```

**Explanation**:
The `main` function initializes the chatbot and starts the conversation loop. It uses the `colorama` library to automatically reset color settings after each print statement, ensuring that the terminal output is visually appealing. The `if __name__ == "__main__":` block ensures that the `main` function is called when the script is executed directly. This is the entry point of the chatbot, where the conversation loop begins, and the user can start interacting with the chatbot.



## Running the Chatbot

To run the chatbot, simply execute the script:

```sh
# Install all dependency such as colorama....
$ pip install -r requirements.txt
# Make sure to set GROQ_API_KEY as env variable 
$ export GROQ_API_KEY=<your-api-key-here>
$ python chat_with_k8s.py
```

You can now interact with your Kubernetes cluster through the chatbot. Ask questions or issue commands, and the chatbot will respond accordingly.

## Demo
1. Run a pod using below command
    ```sh
    kubectl run nginx --image=nginx:latest
    ```
2. Run python script and ask questions regarding your kubernetes clusters.
<Image of demo>

## Conclusion

In this article, we set up a local Kubernetes cluster using Minikube and Docker, and created a Python chatbot that interacts with the cluster using the Groq model. This setup allows for easy interaction with your Kubernetes environment through a conversational interface.
