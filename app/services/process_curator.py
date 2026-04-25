import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agent.curator_agent import CuratorAgent
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def curate_digests(hours: int = 24) -> dict:
    curator = CuratorAgent(USER_PROFILE)
    repo = Repository()
    
    digests = repo.get_recent_digests(hours=hours)
    total = len(digests)
    
    if total == 0:
        logger.warning(f"No digests found from the last {hours} hours")
        return {"total": 0, "ranked": 0}
    
    logger.info(f"Curating {total} digests for {USER_PROFILE['name']}")
    
    # CHANGE: Call 'rank_all_digests' which handles the batches/sleeps internally
    # We pass the full list; the agent will chunk it into 10s and wait 20s between
    ranked_articles = curator.rank_all_digests(digests, batch_size=10)
    
    if not ranked_articles:
        logger.error("Failed to rank digests")
        return {"total": total, "ranked": 0}
    
    logger.info(f"Successfully ranked {len(ranked_articles)} articles")
    
    # Verification and Logging
    print("\n" + "="*30)
    print(f" TOP RECOMMENDATIONS FOR {USER_PROFILE['name'].upper()} ")
    print("="*30)
    
    for i, article in enumerate(ranked_articles[:10], 1):
        # Match ID back to original data for rich logging
        digest = next((d for d in digests if str(d["id"]) == str(article.digest_id)), None)
        if digest:
            # We use 'i' for the display rank because the agent's internal 
            # 'article.rank' is relative to its batch, but 'ranked_articles' 
            # is now globally sorted.
            logger.info(f"\n[#{i}] {digest['title']}")
            logger.info(f"Score: {article.relevance_score}/10 | Reason: {article.reasoning}")
    
    return {
        "total": total,
        "ranked": len(ranked_articles),
        "articles": [
            {
                "digest_id": a.digest_id,
                "rank": i + 1, # Global rank
                "relevance_score": a.relevance_score,
                "reasoning": a.reasoning
            }
            for i, a in enumerate(ranked_articles)
        ]
    }


if __name__ == "__main__":
    result = curate_digests(hours=440)
    print(f"\n=== Curation Results ===")
    print(f"Total digests: {result['total']}")
    print(f"Ranked: {result['ranked']}")
