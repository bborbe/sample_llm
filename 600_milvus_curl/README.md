

https://app.tavily.com/

docker-compose up -d

# ollama pull llama3
ollama pull gemma2:9b

python app.py

curl -X POST http://0.0.0.0:5001/generate \
-H "Content-Type: application/json" \
-d '{"question": "What is LangGraph?"}'
