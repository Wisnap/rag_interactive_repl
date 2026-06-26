# RAG REPL

Interactive Python client for a RAG service. It uses a deterministic local stub
until an API base URL is configured.

```bash
python -m rag_repl
python -m rag_repl --api-url http://localhost:8000
RAG_API_URL=http://localhost:8000 python -m rag_repl
```

Use `/help` in the REPL to list commands. The client sends the fixed
`client_name` value `manual_user` to the API.
