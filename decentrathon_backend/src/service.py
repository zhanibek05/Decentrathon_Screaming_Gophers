import pinecone
from transformers import AutoTokenizer, AutoModel
import torch
from pinecone import Pinecone

from .config import PINECONE_API_KEY

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("screaminggophers")


AutoTokenizer.cache_dir = './temp_cache/'
AutoModel.cache_dir = './temp_cache/'


# Initialize transformer model and tokenizer for embedding
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Function to embed text using Hugging Face model
def embed_text(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1).squeeze().numpy()
    return embeddings

def insert_lecture_materials(docs):
    for idx, doc in enumerate(docs):
        # Create embedding for the document
        embedding = embed_text(doc["content"])
        # Insert the document into Pinecone with metadata
        index.upsert([(str(idx), embedding.tolist(), {"text": doc["content"], "title": doc["title"]})])
        print(f"Inserted document {idx} with metadata: {doc['content']}")

# Example lecture materials to insert
lecture_materials = [
    {"title": "Physics Lecture", "content": "This is a lecture on Newton's Laws of Motion..."},
    {"title": "Math Lecture", "content": "This is a lecture on integrals and derivatives..."},
    {"title": "History Lecture", "content": "This is a lecture on the Roman Empire..."}
]

# Insert lecture materials into Pinecone
#  insert_lecture_materials(lecture_materials)

def retrieve_documents_pinecone(prompt, top_k=1):
    # Embed the prompt to search for relevant documents
    embedding = embed_text(prompt)
    
    # Query Pinecone with the embedding
    query_result = index.query(vector=embedding.tolist(), top_k=top_k, include_metadata=True)
    
    # Print the entire query result to verify it contains matches
    print(query_result)

    # Check if 'matches' are in the result and process them
    if "matches" in query_result and query_result["matches"]:
        documents = []
        for match in query_result["matches"]:
            # Make sure 'metadata' contains 'text'
            if "metadata" in match and "text" in match["metadata"]:
                documents.append(match["metadata"]["text"])
                print(f"Retrieved document: {match['metadata']['text']}")  # Debug print

        # If documents were retrieved, return them
        if documents:
            return documents
        else:
            print("No documents found in the metadata.")
            return None
    else:
        print("No matches found in the query result.")
        return None
