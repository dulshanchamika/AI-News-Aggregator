import os
import time
import logging
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)

# --- Structured Output Schemas ---

class RankedArticle(BaseModel):
    digest_id: str = Field(description="The ID of the digest (article_type:article_id)")
    relevance_score: float = Field(description="Relevance score from 0.0 to 10.0", ge=0.0, le=10.0)
    rank: int = Field(description="Rank position relative to this batch (1 = best)", ge=1)
    reasoning: str = Field(description="Brief explanation of why this aligns with user interests")

class RankedDigestList(BaseModel):
    articles: List[RankedArticle] = Field(description="List of ranked articles")

# --- The Master Curator Prompt ---

CURATOR_PROMPT = """You are an expert AI News Curator. Your goal is to rank a list of AI articles based on their utility and relevance to a specific user profile.

### Ranking Instructions:
1. **Compare & Contrast**: Look at all articles in the batch before assigning ranks.
2. **Scoring Rubric**:
   - 9.0-10.0: Essential reading; directly matches interests and expertise level.
   - 7.0-8.9: High value; very relevant but perhaps less urgent.
   - 5.0-6.9: Interesting; marginal relevance or slightly off-topic.
   - 0.0-4.9: Low relevance; skip-worthy for this specific user.
3. **No Ties**: Every article in a batch must have a unique rank (1, 2, 3...).
4. **Substance over Hype**: Prioritize technical depth and actionable insights over marketing announcements.

### Output Format:
Return a JSON object containing a list of ranked articles."""

# --- Agent Implementation ---

class CuratorAgent:
    def __init__(self, user_profile: dict):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash-lite" 
        self.user_profile = user_profile
        # We combine the Master Prompt with the specific User Data here
        self.system_instruction = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        interests = "\n".join(f"- {i}" for i in self.user_profile.get("interests", []))
        prefs = "\n".join(f"- {k}: {v}" for k, v in self.user_profile.get("preferences", {}).items())
        
        return f"""{CURATOR_PROMPT}

### Target User Profile:
- **Name**: {self.user_profile.get('name')}
- **Background**: {self.user_profile.get('background')}
- **Expertise Level**: {self.user_profile.get('expertise_level')}
- **Core Interests**:
{interests}
- **Delivery Preferences**:
{prefs}"""

    def _chunk_list(self, data: list, size: int):
        for i in range(0, len(data), size):
            yield data[i : i + size]

    def rank_all_digests(self, digests: List[dict], batch_size: int = 10) -> List[RankedArticle]:
        """Processes and ranks articles in batches to enable listwise comparison."""
        if not digests:
            return []

        all_ranked_results = []
        chunks = list(self._chunk_list(digests, batch_size))
        total_batches = len(chunks)

        for idx, chunk in enumerate(chunks, 1):
            logger.info(f"Curating Batch [{idx}/{total_batches}]...")
            
            # Format the batch text
            digest_text = "\n\n".join([
                f"ID: {d['id']}\nTitle: {d['title']}\nSummary: {d['summary']}\nType: {d['article_type']}"
                for d in chunk
            ])
            
            user_prompt = f"Please rank these {len(chunk)} articles for the user:\n\n{digest_text}"

            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        temperature=0.2,
                        response_mime_type="application/json",
                        response_schema=RankedDigestList,
                    ),
                )
                
                if response.parsed and response.parsed.articles:
                    all_ranked_results.extend(response.parsed.articles)

                # Respect Free Tier limits
                if idx < total_batches:
                    logger.info("Waiting for rate limit cooldown...")
                    time.sleep(20)

            except Exception as e:
                logger.error(f"Error ranking batch {idx}: {e}")
                continue

        # Return globally sorted list (highest scores first)
        return sorted(all_ranked_results, key=lambda x: x.relevance_score, reverse=True)