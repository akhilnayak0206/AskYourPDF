# AskYourPDF
RAG AI Agent in Python


uv run uvicorn main:app --reload

<!-- this run what we have defined in create function i guess to the port given below -->
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery

docker run -d -p 6333:6333 -p 6334:6334 --name qdrant qdrant/qdrant:latest