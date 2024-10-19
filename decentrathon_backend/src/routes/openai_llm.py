import json
import os
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from openai import OpenAI
import pandas as pd
from io import BytesIO, StringIO
import csv
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
import pinecone

from ..service import retrieve_documents_pinecone
from ..schemas import EvaluationRequest
from ..config import YOUR_HF_TOKEN
from .faster_whisper import convert_mp4_to_mp3, speech_to_text_pipeline


router = APIRouter()

client = OpenAI()


class LLMRequest(BaseModel):
    prompt: str
    pupil_text: str

#  @router.post("/evaluate/")
async def get_answer(request: LLMRequest):
    try:
        # Retrieve relevant documents from Pinecone
        prompt = request.prompt
        pupil_text = request.pupil_text
        retrieved_docs = retrieve_documents_pinecone(prompt)
        retrieved_context = "\n".join(retrieved_docs)

        # Remove all double quotes from the prompt and pupil_text
        sanitized_prompt = prompt.replace('"', '')
        sanitized_pupil_text = pupil_text.replace('"', '')

        # Pass the retrieved information along with the sanitized prompt and pupil's text
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a teacher assistant. You have access to the following documents to help evaluate the pupil's text: {retrieved_context}. Ensure the pupil's text matches the teacher's lecture."
                },
                {
                    "role": "user",
                    "content": f'I am a teacher and here is information about the lecture and subject: {sanitized_prompt}.'
                },
                {
                    "role": "user",
                    "content": f'Here is the pupil\'s text: {sanitized_pupil_text}.'
                }
            ]
        )

        # Correct way to access the response content
        return {"text": completion.choices[0].message.content}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



#  @router.post("/score")
async def get_answer_score(request: LLMRequest):
    
    prompt = request.prompt
    pupil_text = request.pupil_text
    retrieved_docs = retrieve_documents_pinecone(prompt)
    retrieved_context = "\n".join(retrieved_docs)

    # Remove all double quotes from the prompt and pupil_text
    sanitized_prompt = prompt.replace('"', '')
    sanitized_pupil_text = pupil_text.replace('"', '')
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f'You are getting text from video where people sit in lesson. You are teacher assistant and you need to return number mark. Its important that pupils text must match to the teachers lecture. Return only mark number where 10 is max.'
            },
            {
                "role": "user",
                "content": f'I am a teacher and here is information about lecture and subject: {prompt}.'
            },
            {
                "role": "user",
                "content": f'Here is pupils text: {pupil_text}.'
            }
        ]
    )

    return {"text": completion.choices[0].message.content}


LOCAL_VIDEO_PATH = r"C:\Users\Zhanibek\Desktop\sanzhik_decentrathon\screaming_gophers\videos"


@router.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Save uploaded video to local storage
        video_path = os.path.join(LOCAL_VIDEO_PATH, file.filename)
        
        # Ensure the directory exists
        os.makedirs(LOCAL_VIDEO_PATH, exist_ok=True)
        
        with open(video_path, "wb") as video_file:
            video_file.write(await file.read())

        return {"message": f"{file.filename}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DownloadCSVRequest(BaseModel):
    video_file: str
    prompt: str

@router.post("/download-csv/")
async def download_csv(request: DownloadCSVRequest):
    # Extract video_file and prompt from the request body
    video_file = os.path.join(LOCAL_VIDEO_PATH, request.video_file)
    prompt = request.prompt
    
    # Create a CSV in-memory using StringIO
    output = StringIO()
    writer = csv.writer(output)
    
    # Convert video to audio file (MP4 to MP3)
    audio_file = f"{video_file[:-5]}.mp3"
    print(audio_file)
    
    convert_mp4_to_mp3(video_file, audio_file)
    
    model_path = r"C:\Users\Zhanibek\Desktop\sanzhik_decentrathon\peach_to_text\models\models--Systran--faster-whisper-large-v3\snapshots\edaa852ec7e145841d8ffdb056a99866b5f0a478"
    writer.writerow(['Speaker', 'Mark', 'Comment(Feedback)'])
    
    # Speech to text conversion
    result = speech_to_text_pipeline(audio_file, model_path, YOUR_HF_TOKEN)
    
    # Process each segment
    for res in result['segments']:
        print(res['speaker'], res['text'], res['start'], res['end'])
        
        llm_request = LLMRequest(
            prompt=prompt, 
            pupil_text=res['text']
        )
        # Get comments and scores based on the prompt and pupil's text
        comment = await get_answer(llm_request)  # Comment (feedback)
        score = await get_answer_score(llm_request)  # Score (mark)

        # Write rows to the CSV
        writer.writerow([res['speaker'], score['text'], comment['text']])
    
    # Get the CSV content
    output.seek(0)
    csv_content = output.getvalue()

    # Return the CSV file as a response
    headers = {
        'Content-Disposition': 'attachment; filename="table.csv"',
        'Content-Type': 'text/csv'
    }

    return Response(content=csv_content, headers=headers)