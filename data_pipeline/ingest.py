import json
from elasticsearch import Elasticsearch
from google.cloud import aiplatform
import os
from vertexai.language_models import TextEmbeddingModel
import time
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

CLOUD_ID = os.getenv("ELASTIC_CLOUD_ID")
API_KEY = os.getenv("ELASTIC_API_KEY")
GOOGLE_PROJECT_ID = "career-compass-473512"
GOOGLE_LOCATION = "us-central1"

INDEX_NAME = "career_knowledge_base"

# Global variable to store the initialized model instance
EMBEDDING_MODEL = None


def get_batch_embeddings(texts: list[str]) -> list[list[float]]:
    """Gets vector embeddings for a list of texts using Google's Vertex AI."""
    global EMBEDDING_MODEL

    # Initialize model if it hasn't been already
    if EMBEDDING_MODEL is None:
        aiplatform.init(project=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)
        EMBEDDING_MODEL = TextEmbeddingModel.from_pretrained("text-embedding-004")

    # Process the entire list in one go
    embeddings = EMBEDDING_MODEL.get_embeddings(texts)

    # Extract the list of vectors
    return [e.values for e in embeddings]


def main():
    print("Connecting to Elastic Cloud...")
    try:
        client = Elasticsearch(cloud_id=CLOUD_ID, api_key=API_KEY)
        client.info()
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return

    try:
        # --- Index Setup ---
        if client.indices.exists(index=INDEX_NAME):
            print(f"Deleting old index '{INDEX_NAME}'...")
            client.indices.delete(index=INDEX_NAME)

        print(f"Creating new index '{INDEX_NAME}'...")
        client.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": 768  # text-embedding-004 is 768 dimensions
                    },
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "category": {"type": "keyword"}
                }
            }
        )

        # --- Data Loading ---
        print("Reading career data from career_data.json...")
        with open("career_data.json", "r", encoding="utf-8") as f:
            documents = json.load(f)

        total_docs = len(documents)
        print(f"Starting embedding generation for {total_docs} documents (in a single batch)...")

        texts_to_embed = [doc["content"] for doc in documents]

        # --- Single Batch Processing ---
        all_embeddings = get_batch_embeddings(texts_to_embed)

        if len(all_embeddings) != total_docs:
            raise RuntimeError("Embedding generation failed: Mismatched number of results.")

        # --- Document Preparation for Bulk Upload ---
        operations = []
        for doc_index, doc in enumerate(documents):
            doc["content_vector"] = all_embeddings[doc_index]

            operations.append({"index": {"_index": INDEX_NAME}})
            operations.append(doc)

        # --- Elasticsearch Bulk Upload ---
        if operations:
            print("\nUploading documents to Elastic...")
            response = client.bulk(operations=operations, refresh=True)

            if response.get("errors"):
                print("There were errors during the bulk upload.")
            else:
                print("\n-----------------------------------------")
                print(f" Successfully uploaded {total_docs} documents! ")
                print("-----------------------------------------")

    except Exception as e:
        print("\n--- FATAL ERROR ---")
        print(f"An error occurred: {e}")
        print("--- END FATAL ERROR ---")


if __name__ == "__main__":
    main()
