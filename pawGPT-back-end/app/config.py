from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone

import os

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/paw-gpt-db")

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")
NAMESPACE_NAME = os.environ.get("PINECONE_NAMESPACE_NAME")
index = pc.Index(INDEX_NAME)

ai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
SYSTEM_INSTRUCTION = (
	"You are PawGPT, an advanced and compassionate veterinary AI assistant. "
    "Your task is to answer the user's question accurately using only the provided context from veterinary manuals. "
    "If the answer cannot be found in the context, politely state that you don't have that specific data in your manuals. "
    "Always maintain a professional, helpful tone."
)

with open("certs/private_key.pem", "r") as f:
    PRIVATE_KEY = f.read()

with open("certs/public_key.pem", "r") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES: int = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_DAYS: int = os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS")