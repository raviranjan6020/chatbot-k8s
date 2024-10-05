# chatbot-k8s
A chatbot that can chat with your Kubernetes cluster.
It uses groq to generate responses, and Groq's function calling to interact with the Kubernetes cluster.

[https://www.codereliant.io/chat-with-your-kubernetes-cluster/](https://console.groq.com/docs/quickstart)


### Set up
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run
```
export GROQ_API_KEY=<your-api-key-here>
python chat_with_k8s.py
```
