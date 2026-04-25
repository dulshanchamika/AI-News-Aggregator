import time
from typing import Optional, List
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agent.digest_agent import DigestAgent
from app.database.repository import Repository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def chunk_list(data: list, size: int):
    """Break a list into smaller chunks."""
    for i in range(0, len(data), size):
        yield data[i:i + size]

def process_digests(limit: Optional[int] = None, batch_size: int = 5) -> dict:
    # Use the batch-capable version of DigestAgent
    agent = DigestAgent() 
    repo = Repository()
    
    articles = repo.get_articles_without_digest(limit=limit)
    total = len(articles)
    processed = 0
    failed = 0
    
    logger.info(f"Starting batch digest processing for {total} articles (Batch Size: {batch_size})")
    
    # Split the 47 articles into chunks of 5
    article_chunks = list(chunk_list(articles, batch_size))
    total_batches = len(article_chunks)

    for b_idx, chunk in enumerate(article_chunks, 1):
        logger.info(f"Processing Batch [{b_idx}/{total_batches}] containing {len(chunk)} articles...")
        
        try:
            # Note: You'll need to update your DigestAgent to have a 'generate_batch_digest' method
            # as shown in our previous discussion.
            batch_results = agent.generate_batch_digest(chunk)
            
            if batch_results:
                # Map the generated digests back to their original IDs
                # We assume the AI returns them in the same order
                for i, digest in enumerate(batch_results):
                    original_article = chunk[i]
                    repo.create_digest(
                        article_type=original_article["type"],
                        article_id=original_article["id"],
                        url=original_article["url"],
                        title=digest.title,
                        summary=digest.summary,
                        published_at=original_article.get("published_at")
                    )
                    processed += 1
                
                logger.info(f"✓ Successfully processed batch {b_idx}")
            else:
                failed += len(chunk)
                logger.warning(f"✗ Failed to generate digests for batch {b_idx}")
                
        except Exception as e:
            failed += len(chunk)
            logger.error(f"✗ Critical error in batch {b_idx}: {e}")
        
        # Add a mandatory sleep between batches to avoid the RPM limit
        if b_idx < total_batches:
            logger.info("Sleeping for 10 seconds to respect Free Tier limits...")
            time.sleep(20)
    
    logger.info(f"Processing complete: {processed} processed, {failed} failed out of {total} total")
    
    return {
        "total": total,
        "processed": processed,
        "failed": failed
    }

if __name__ == "__main__":
    result = process_digests()
    print(f"\nFinal Summary:")
    print(f"Total articles: {result['total']}")
    print(f"Processed: {result['processed']}")
    print(f"Failed: {result['failed']}")