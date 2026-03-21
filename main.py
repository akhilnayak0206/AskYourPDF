import logging
from fastapi import FastAPI

import inngest
import inngest.fast_api
from inngest.experimental import ai

from dotenv import load_dotenv

import os
import datetime
import uuid


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
    fn_id="RAG: Capture PDF",
    trigger=inngest.TriggerEvent(event="rag/capture_pdf")
    
)
async def rag_capture_pdf(ctx: inngest.Context):
    return {"message": "PDF captured"}

app = FastAPI()


inngest.fast_api.serve(app, inngest_client,[rag_capture_pdf])