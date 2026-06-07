from app.config import ai_client
from app.config import GEMINI_MODEL
from app.config import index
from app.config import NAMESPACE_NAME
from app.config import SYSTEM_INSTRUCTION
from app.utils import get_current_user
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel

class QueryRequest(BaseModel):
	question: str
	top_k: int = 3

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    
router = APIRouter()

@router.post("", response_model=QueryResponse)
async def handle_rag_query(request: QueryRequest, current_user: dict = Depends(get_current_user)):
	"""Takes a user question, queries the integrated Pinecone index using serverless text input, extracts the matching manual contexts, and passes it to Gemini 3.0 Flash.

	Args:
		request (QueryRequest): request object
	"""

	if not request.question.strip():
		raise HTTPException(status_code=400, detail="Question cannot be empty")

	try:
		query_payload = {
			"inputs": {
				"text": request.question
			},
			"top_k": request.top_k
		}

		search_results = index.search(namespace=NAMESPACE_NAME, query=query_payload)

		retrieved_context_blocks = []
		sources_metadata = []

		hits: list = search_results.get("result").get("hits")
		if not hits:
			retrieved_context_blocks.append("No specific manual context found")
		else:
			for hit in hits:
				fields = hit.get("fields", {})
				text_content = fields.get("text", "")
				source_file = fields.get("source_file", "Unknown Source")
				pages = fields.get("pages", [])
                
				retrieved_context_blocks.append(text_content)
				sources_metadata.append({
                    "file": source_file,
                    "pages": pages
                })

		context_str = "\n\n---\n\n".join(retrieved_context_blocks)

		augmented_prompt = f"Context from manuals:\n{context_str}\n\nUser Question: {request.question}"

		gemini_response = ai_client.models.generate_content(
			model=GEMINI_MODEL,
			contents=augmented_prompt,
			config={"system_instruction": SYSTEM_INSTRUCTION}
		)
  
		return QueryResponse(
			answer=gemini_response.text,
			sources=sources_metadata
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Internal RAG pipline error: {str(e)}")