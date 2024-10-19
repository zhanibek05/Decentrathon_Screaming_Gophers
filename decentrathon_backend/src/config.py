from dotenv import load_dotenv
import os
import boto3


load_dotenv()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
YOUR_HF_TOKEN = os.getenv("YOUR_HF_TOKEN")

s3_client = boto3.client('s3')
