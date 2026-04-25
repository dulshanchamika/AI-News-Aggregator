import os
import time
import logging
from typing import Optional, List
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Schema for a single digest
class DigestOutput(BaseModel):
    title: str
    summary: str

# New schema to receive a list from Gemini
class BatchDigestOutput(BaseModel):
    digests: List[DigestOutput]

PROMPT = """You are an expert AI news analyst. 
I will provide a list of articles. For EACH article:
1. Create a compelling title (5-10 words).
2. Write a 2-3 sentence summary highlighting main points and implications.
Return the results as a JSON list of objects."""

class DigestAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=3,
                    initial_delay=10.0, # Increased delay for free tier
                    http_status_codes=[429, 500, 503]
                )
            )
        )
        self.model = "gemini-2.5-flash"

    def generate_batch_digest(self, articles: List[dict]) -> List[DigestOutput]:
        """
        Processes a list of articles (e.g., 5 at a time) to save quota.
        Each article dict should have 'title', 'content', and 'type'.
        """
        # Format the batch for the prompt
        formatted_articles = ""
        for i, art in enumerate(articles):
            formatted_articles += f"\n--- Article {i+1} ---\n"
            formatted_articles += f"Type: {art['type']}\nTitle: {art['title']}\nContent: {art['content'][:4000]}\n"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=formatted_articles,
                config=types.GenerateContentConfig(
                    system_instruction=PROMPT,
                    temperature=0.7,
                    response_mime_type="application/json",
                    response_schema=BatchDigestOutput,
                ),
            )
            
            # Larger sleep after a big batch
            time.sleep(10) 
            
            return response.parsed.digests

        except errors.APIError as e:
            logger.error(f"Batch API Error: {e.message}")
            return []
        except Exception as e:
            logger.error(f"Unexpected Batch error: {str(e)}")
            return []