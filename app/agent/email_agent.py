import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# --- Schema Definitions (Matching your existing structure) ---

class EmailIntroduction(BaseModel):
    greeting: str = Field(description="Personalized greeting with user's name and date")
    introduction: str = Field(description="2-3 sentence overview of what's in the top 10 ranked articles")

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
2. Provide a 2-3 sentence overview of the top articles provided.
3. Highlight the most significant technical themes or breakthroughs.
4. Maintain a friendly yet professional tone suitable for an AI Engineer."""

class EmailAgent:
    def __init__(self, user_profile: dict):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
        self.user_profile = user_profile

    def generate_introduction(self, ranked_articles: List) -> EmailIntroduction:
        current_date = datetime.now().strftime('%B %d, %Y')
        
        if not ranked_articles:
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your daily AI update for {current_date}.",
                introduction="We couldn't find any specific articles matching your profile today, but stay tuned for more updates soon!"
            )
        
        # Prepare the context for Gemini to summarize the "theme" of the day
        article_summaries = "\n".join([
            f"- {a.title if hasattr(a, 'title') else a.get('title', 'N/A')}"
            for a in ranked_articles[:10]
        ])
        
        user_prompt = f"""User: {self.user_profile['name']}
Date: {current_date}

Top Articles Today:
{article_summaries}

Generate the greeting and a 2-3 sentence technical overview."""

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
            
            return response.parsed

        except Exception as e:
            print(f"Error generating introduction: {e}")
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your daily AI update for {current_date}.",
                introduction="Here is a curated selection of the most relevant AI research and production updates for your profile."
            )

    def create_email_digest_response(self, ranked_articles: List[RankedArticleDetail], total_ranked: int, limit: int = 10) -> EmailDigestResponse:
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)
        
        return EmailDigestResponse(
            introduction=introduction,
            articles=top_articles,
            total_ranked=total_ranked,
            top_n=limit
        )