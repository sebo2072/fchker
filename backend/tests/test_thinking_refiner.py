import asyncio
import logging
import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.thinking_refiner import ThinkingRefiner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_refiner():
    print("\n--- TEST: NARRATIVE THINKING REFINER (STREAMING) ---\n")
    
    results = []
    current_message = ""
    
    async def progress_callback(update):
        nonlocal current_message
        if update.get("is_delta"):
            # In a real UI, we append or replace. For terminal, we show the delta or just current state
            delta = update.get("message")[len(current_message):]
            if delta:
                print(delta, end="", flush=True)
                current_message = update.get("message")
        elif update.get("is_streaming_complete"):
            print("\n[STREAM COMPLETE]")
            # Log final message length
            msg = update.get("message", "")
            print(f"Final Message Length: {len(msg)} chars")
            results.append(update)
            current_message = ""
        elif update.get("is_raw_fallback"):
            print(f"\n[FALLBACK]: {update.get('message')}")
            results.append(update)

    refiner = ThinkingRefiner(
        session_id="test_session",
        claim_id="test_claim",
        progress_callback=progress_callback
    )

    # Simulated raw thinking chunks that will exceed the 500 char buffer
    raw_thought_chunks = [
        "Analyzing the provided text to extract core verifiable claims. I am looking for specific dates, names, and numerical values that can be cross-referenced with public records. ",
        "Specifically, I am focusing on the mention of Parth Pawar and the Pune land deal. I need to verify if the Rs 1,800 crore figure is a market valuation or an alleged price. ",
        "Searching for the Kharge Committee report details. It is reported to be quite lengthy, possibly around 1,000 pages. I need to confirm the exact content and if it mentions procedural lapses. ",
        "The report reportedly gives a clean chit to certain individuals but recommends action against others. I must distinguish between 'procedural lapses' and 'criminal intent'. ",
        "Finalizing the extraction of all 13 claims. Ensuring each claim is tied to its original context in the text for accurate verification in the next phase. "
    ]

    print("Feeding raw thoughts to refiner...")
    for chunk in raw_thought_chunks:
        print(f"\n[INPUT CHUNK SENT]: {chunk[:50]}...")
        await refiner.add_raw_thought(chunk)
        # Delay to allow processing
        await asyncio.sleep(0.5)

    print("\n\nFlushing refiner...")
    await refiner.flush()
    
    print(f"\n\nTotal refined updates generated: {len(results)}")
    
    if len(results) > 0:
        print("\n[SUCCESS] Narrative Refiner Agent is WORKING.")
    else:
        print("\n[FAILURE] Narrative Refiner Agent FAILED to generate updates.")

if __name__ == "__main__":
    asyncio.run(test_refiner())
