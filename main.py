import logging
from fastapi import FastAPI

import inngest
import inngest.fast_api
from inngest.experimental import ai

from dotenv import load_dotenv

import os
import datetime
import uuid

from data_loader import load_and_chunk_pdf, embed_text
from vector_db import QdrantStorage
from custom_types import (
    RAGChunkAndSrc,
    RAGUpsertResult,
    RAGSearchResults,
    RAGQueryResult,
)

load_dotenv()

inngest_client = inngest.Inngest(
    app_id="ask_your_pdf",
    logger=logging.getLogger("uvicorn"),
    # for production there is a bit more security required
    is_production=os.getenv("ENV") == "production",
    # it support pydantic
    serializer=inngest.PydanticSerializer(),
)


# capture the pdf from FE and then send it to API
@inngest_client.create_function(
    fn_id="RAG: Capture PDF", trigger=inngest.TriggerEvent(event="rag/capture_pdf")
)
async def rag_capture_pdf(ctx: inngest.Context):

    def _load(ctx: inngest.Context) -> RAGChunkAndSrc:
        pdf_path = ctx.event.data.get("pdf_path")
        source_id = ctx.event.data.get("source_id", pdf_path)
        chunks = load_and_chunk_pdf(pdf_path)
        return RAGChunkAndSrc(chunks=chunks, source_id=source_id)

    def _upsert(chunks_and_src: RAGChunkAndSrc) -> RAGUpsertResult:
        chunks = chunks_and_src.chunks
        source_id = chunks_and_src.source_id
        vecs = embed_text(chunks)
        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, name=f"{source_id}:{i}"))
            for i in range(len(chunks))
        ]
        payloads = [
            {"source": source_id, "text": chunks[i]} for i in range(len(chunks))
        ]
        QdrantStorage().upsert(ids, vecs, payloads)

        return RAGUpsertResult(ingested=len(chunks))

    chunks_and_src: RAGChunkAndSrc = await ctx.step.run(
        "load-and-chunk", lambda: _load(ctx), output_type=RAGChunkAndSrc
    )

    ingested = await ctx.step.run(
        "embed-and-upsert", lambda: _upsert(chunks_and_src), output_type=RAGUpsertResult
    )

    return ingested.model_dump()


# query/ask from pdf
@inngest_client.create_function(
    fn_id="RAG: Query PDF", trigger=inngest.TriggerEvent(event="rag/query_pdf_ai")
)
async def rag_query_pdf(ctx: inngest.Context):
    def _search(question: str, top_k: int = 5) -> RAGSearchResults:
        vec = embed_text([question])[0]
        results = QdrantStorage().search(vec, limit=top_k)
        return RAGSearchResults(results=results)


app = FastAPI()


inngest.fast_api.serve(app, inngest_client, [rag_capture_pdf])
