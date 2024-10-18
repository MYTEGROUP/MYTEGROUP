import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

from openaiconfig.openaiservice import OpenAIService
from helpers.helper import load_json, save_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename='fact_checking.log',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FactChecker:
    def __init__(self, discussion_file: str):
        """
        Initialize the FactChecker with the path to the discussion threads JSON file.
        """
        self.discussion_file = discussion_file
        self.openai_service = OpenAIService()
        self.executor = ThreadPoolExecutor(max_workers=10)  # Handle concurrency

    async def fact_check_claims(self):
        """
        Main method to fact-check all unverified claims in the discussion threads.
        """
        loop = asyncio.get_event_loop()
        try:
            # Load discussion threads from JSON file asynchronously
            data = await loop.run_in_executor(self.executor, load_json, self.discussion_file)
        except Exception as e:
            logging.error(f"Failed to load discussion threads: {e}")
            return

        claims = self.extract_claims(data)
        if not claims:
            logging.info("No unverified claims found.")
            return

        # Create tasks for concurrent fact-checking
        tasks = [
            asyncio.create_task(self.process_claim(thread_id, comment_id, claim))
            for thread_id, comment_id, claim in claims
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        try:
            # Save the updated discussion threads back to the JSON file
            await loop.run_in_executor(self.executor, save_json, self.discussion_file, data)
            logging.info("Discussion threads updated with fact-check results.")
        except Exception as e:
            logging.error(f"Failed to save updated discussion threads: {e}")

    def extract_claims(self, data: Dict) -> List[tuple]:
        """
        Extract unverified claims from the discussion threads.
        Returns a list of tuples containing thread_id, comment_id, and the claim.
        """
        claims = []
        for thread in data.get('threads', []):
            for comment in thread.get('comments', []):
                if comment.get('claim') and not comment.get('fact_checked'):
                    claims.append((thread['id'], comment['id'], comment['claim']))
        return claims

    async def process_claim(self, thread_id: str, comment_id: str, claim: str):
        """
        Process a single claim: verify it and update the discussion thread with the result.
        """
        loop = asyncio.get_event_loop()
        try:
            # Verify the claim using OpenAI services
            result = await loop.run_in_executor(self.executor, self.openai_service.verify_claim, claim)
        except Exception as e:
            logging.error(f"Error verifying claim '{claim}': {e}")
            return

        try:
            # Update the claim result in the discussion threads
            await loop.run_in_executor(self.executor, self.update_discussion, thread_id, comment_id, result)
            logging.info(f"Claim '{claim}' fact-checked successfully.")
        except Exception as e:
            logging.error(f"Error updating discussion for claim '{claim}': {e}")

    def update_discussion(self, thread_id: str, comment_id: str, result: Dict):
        """
        Update the specific comment in the discussion thread with the fact-check result.
        """
        data = load_json(self.discussion_file)
        for thread in data.get('threads', []):
            if thread['id'] == thread_id:
                for comment in thread.get('comments', []):
                    if comment['id'] == comment_id:
                        comment['fact_checked'] = True
                        comment['fact_check_result'] = result
                        break
        save_json(self.discussion_file, data)

    async def run(self):
        """
        Run the fact-checking process asynchronously.
        """
        await self.fact_check_claims()

if __name__ == '__main__':
    fact_checker = FactChecker('storage/DiscussionThreads.json')
    asyncio.run(fact_checker.run())