from typing import List
import uuid
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import NoCredentialsError
from pydantic import BaseModel

from .schemas import EvaluationRequest
from .service import insert_lecture_materials, retrieve_documents_pinecone
from .config import AWS_REGION, S3_BUCKET_NAME, s3_client
from .routes import openai_llm

app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=['Content-Type', 'Authorization','Access-Control-Allow-Origin', "*"]
)



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    try:
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_contents = await file.read()
        res = s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=unique_filename, Body=file_contents, ACL="public-read")
        image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        return {"image_url": image_url, "file_url": unique_filename, "status": "Successful"}
    except (NoCredentialsError):
        raise HTTPException(status_code=500, detail="AWS credentials not configured properly")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


class LectureMaterial(BaseModel):
    lecture_materials: List[dict]


@app.post("/insert_lecture/")
def insert_lecture(lecture_materials: LectureMaterial):
    return insert_lecture_materials(lecture_materials.lecture_materials)


@app.post("/retrieve/")
def retrieve_lecture(prompt: EvaluationRequest):
    return retrieve_documents_pinecone(prompt.prompt)


app.include_router(openai_llm.router, prefix="/llm", tags=["llm"])
#  app.include_router(faster_whisper.router, prefix="/faster_whisper", tags=["faster_whisper"])
