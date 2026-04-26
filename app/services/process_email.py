import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ensure the app directory is in the path
sys.path.insert(0, os.getcwd())
load_dotenv()

from app.agent.email_agent import EmailAgent, RankedArticleDetail, EmailDigestResponse
from app.agent.curator_agent import CuratorAgent
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository
from app.services.email_service import send_email, digest_to_html

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def generate_email_digest(hours: int = 24, top_n: int = 10) -> EmailDigestResponse:
    # 1. Initialize Agents & Repo
    curator = CuratorAgent(USER_PROFILE)
    email_agent = EmailAgent(USER_PROFILE)
    repo = Repository()
    
    # 2. Fetch raw data
    digests = repo.get_unsent_digests(hours=hours)
    total = len(digests)
    
    if total == 0:
        logger.warning(f"No digests found from the last {hours} hours")
        raise ValueError("No digests available for the requested timeframe.")
    
    # 3. Rank articles (Using the BATCHED Gemini method)
    logger.info(f"Ranking {total} digests for {USER_PROFILE['name']}...")
    # UPDATED: Calling 'rank_all_digests' to handle internal batching and rate limits
    ranked_results = curator.rank_all_digests(digests, batch_size=10)
    
    if not ranked_results:
        logger.error("Failed to rank digests")
        raise ValueError("Ranking process returned no results.")
    
    # 4. Map ranked results back to full article metadata
    article_details = []
    for a in ranked_results:
        # String comparison ensures matching even if DB returns ints and AI returns strings
        original = next((d for d in digests if str(d["id"]) == str(a.digest_id)), None)
        
        if original:
            article_details.append(
                RankedArticleDetail(
                    digest_id=str(a.digest_id),
                    rank=a.rank,
                    relevance_score=a.relevance_score,
                    reasoning=a.reasoning,
                    title=original.get("title", "No Title"),
                    summary=original.get("summary", "No Summary"),
                    url=original.get("url", "#"),
                    article_type=original.get("article_type", "Article")
                )
            )

    # 5. Generate the personalized email introduction
    logger.info(f"Generating email intro for top {top_n} articles...")
    email_digest = email_agent.create_email_digest_response(
        ranked_articles=article_details,
        total_ranked=len(ranked_results),
        limit=top_n
    )
    
    return email_digest

def send_digest_email(hours: int = 24, top_n: int = 10) -> dict:
    try:
        # Generate the structured digest
        result = generate_email_digest(hours=hours, top_n=top_n)
        
        # Prepare content formats
        markdown_content = result.to_markdown()
        html_content = digest_to_html(result)
        
        # Clean subject line
        clean_date = result.introduction.greeting.split('for ')[-1] if 'for ' in result.introduction.greeting else 'Today'
        subject = f"Daily AI News Digest - {clean_date}"
        
        # Dispatch email
        send_email(
            subject=subject,
            body_text=markdown_content,
            body_html=html_content
        )
        
        # Mark as sent in DB
        repo = Repository()
        digest_ids_to_mark = [a.digest_id for a in result.articles]
        if digest_ids_to_mark:
            repo.mark_digests_as_sent(digest_ids_to_mark)
        
        return {
            "success": True,
            "subject": subject,
            "articles_count": len(result.articles)
        }
        
    except Exception as e:
        logger.error(f"Critical error in email workflow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    outcome = send_digest_email(hours=72, top_n=10)
    print(f"\nFinal Outcome: {'SUCCESS' if outcome['success'] else 'FAILED'}")