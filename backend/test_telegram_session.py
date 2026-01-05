"""Test script to verify Telegram session is valid."""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID'))
API_HASH = os.getenv('TELEGRAM_API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
GROUP_ID = int(os.getenv('TELEGRAM_GROUP_ID'))


async def test_session():
    """Test if the Telegram session is valid and authorized."""
    print(f"Testing Telegram session...")
    print(f"API ID: {API_ID}")
    print(f"Group ID: {GROUP_ID}")
    print(f"Session String: {SESSION_STRING[:50]}...")

    try:
        # Create client
        client = TelegramClient(
            StringSession(SESSION_STRING),
            API_ID,
            API_HASH
        )

        # Connect
        print("\nConnecting to Telegram...")
        await client.connect()
        print("[OK] Connected successfully")

        # Check authorization
        print("\nChecking authorization...")
        is_authorized = await client.is_user_authorized()

        if not is_authorized:
            print("[FAIL] Session is NOT authorized - session expired or invalid")
            await client.disconnect()
            return False

        print("[OK] Session is authorized")

        # Get current user info
        print("\nGetting user info...")
        me = await client.get_me()
        print(f"[OK] Logged in as: {me.first_name} (@{me.username})")
        print(f"  Phone: {me.phone}")

        # Try to get group info
        print(f"\nGetting group info for ID: {GROUP_ID}...")
        try:
            entity = await client.get_entity(GROUP_ID)
            print(f"[OK] Found group: {getattr(entity, 'title', 'Unknown')}")
            print(f"  Type: {type(entity).__name__}")

            # Try to get recent messages
            print(f"\nFetching last 5 messages from the group...")
            messages = await client.get_messages(entity, limit=5)
            print(f"[OK] Retrieved {len(messages)} messages")

            for i, msg in enumerate(messages, 1):
                if msg.text:
                    preview = msg.text[:50].replace('\n', ' ')
                    print(f"  {i}. {preview}...")
                else:
                    print(f"  {i}. [Non-text message]")

        except Exception as e:
            print(f"[FAIL] Error getting group info: {e}")
            await client.disconnect()
            return False

        # Disconnect
        await client.disconnect()
        print("\n[OK] All checks passed - session is valid!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_session())
    exit(0 if result else 1)
