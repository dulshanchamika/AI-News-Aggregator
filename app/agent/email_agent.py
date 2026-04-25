import os
import time  # Essential for rate-limit management
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

import logging

logger = logging.getLogger(__name__)

load_dotenv()

# --- Schema Definitions ---

class EmailIntroduction(BaseModel):
    greeting: str = Field(description="Personalized greeting with user's name and date")
    introduction: str = Field(description="2-3 sentence overview of the technical themes in the top articles")

class RankedArticleDetail(BaseModel):
    digest_id: str
    rank: int
    relevance_score: float
    title: str
    summary: str
    url: str
    article_type: str
    reasoning: Optional[str] = None

class EmailDigestResponse(BaseModel):
    introduction: EmailIntroduction
    articles: List[RankedArticleDetail]
    total_ranked: int
    top_n: int
    
    def to_markdown(self) -> str:
        markdown = f"## {self.introduction.greeting}\n\n"
        markdown += f"{self.introduction.introduction}\n\n"
        markdown += "---\n\n"
        
        for article in self.articles:
            markdown += f"### {article.title}\n"
            markdown += f"**Relevance Score:** {article.relevance_score:.1f}/10\n\n"
            markdown += f"{article.summary}\n\n"
            if article.reasoning:
                markdown += f"> **Why this matters for you:** {article.reasoning}\n\n"
            markdown += f"[Read more →]({article.url})\n\n"
            markdown += "---\n\n"
        
        return markdown

# --- Agent Implementation ---

EMAIL_PROMPT = """You are an expert email writer. Create a warm, professional introduction for a daily AI news digest.
Instructions:
1. Greet the user by name and mention today's date.
2. Provide a 2-3 sentence technical overview of the top articles provided.
3. Highlight significant technical themes or breakthroughs.
4. Maintain a professional tone suitable for an Advanced AI Engineer."""

class EmailAgent:
    def __init__(self, user_profile: dict):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # FIX: Using 1.5-flash to utilize a separate quota bucket from the Curator
        self.model = "gemini-2.5-flash-lite"
        self.user_profile = user_profile

    def generate_introduction(self, ranked_articles: List) -> EmailIntroduction:
        current_date = datetime.now().strftime('%B %d, %Y')
        
        # FIX: Mandatory cooldown sleep (10s) before calling the email agent
        # This prevents "Too Many Requests" if the curator just finished a batch.
        logger.info("EmailAgent: Cooling down for 10 seconds before generating intro...")
        time.sleep(10)
        
        if not ranked_articles:
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your daily AI update for {current_date}.",
                introduction="No specific articles matched your profile today, but we're keeping an eye out for fresh updates."
            )
        
        article_summaries = "\n".join([
            f"- {a.title if hasattr(a, 'title') else a.get('title', 'N/A')}"
            for a in ranked_articles[:10]
        ])
        
        user_prompt = f"""User Profile: {self.user_profile['name']}
Date: {current_date}
Top Articles for today:
{article_summaries}

Please generate the structured greeting and technical overview."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=EMAIL_PROMPT,
                    temperature=0.7,
                    response_mime_type="application/json",
                    response_schema=EmailIntroduction,
                ),
            )
            
            if response.parsed:
                return response.parsed
            raise ValueError("Empty response from Gemini")

        except Exception as e:
            # Enhanced Error Handling for Quota Issues
            logger.error(f"Error generating introduction: {e}")
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your AI news digest for {current_date}.",
                introduction="Here is a curated selection of technical breakthroughs and research updates tailored to your expertise."
            )

    def create_email_digest_response(self, ranked_articles: List[RankedArticleDetail], total_ranked: int, limit: int = 10) -> EmailDigestResponse:
        # Optimization: Only pass exactly what's needed for the intro to keep the prompt small
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)
        
        return EmailDigestResponse(
            introduction=introduction,
            articles=top_articles,
            total_ranked=total_ranked,
            top_n=limit
        )