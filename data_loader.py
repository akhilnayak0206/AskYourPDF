from openai import OpenAI
from llama_index.readers.file import PDFReader
from llama_index.core.node_parser import SentenceSplitter

from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("API_KEY")
)
EMBED_MODEL = "embed-english-v3.0"
EMBED_DIMENSION = 1024

splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)


def load_and_chunk_pdf(file_path: str):
    loader = PDFReader()
    documents = loader.load_data(file=file_path)
    texts = [d.text for d in documents if getattr(d, "text", None)]
    chunks=[]
    for text in texts:
        chunks.extend(splitter.split_text(text))
    return chunks
    
def embed_text(texts: list[str]) -> list[list[float]]:
    responses = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    )
    return [response.embedding for response in responses.data]