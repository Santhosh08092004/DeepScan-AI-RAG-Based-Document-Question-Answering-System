from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil

from query_data import query_rag

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    with open(f"data/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "uploaded"}

@app.post("/query")
def query(query: Query):
    answer = query_rag(query.question)
    return {"answer": answer}