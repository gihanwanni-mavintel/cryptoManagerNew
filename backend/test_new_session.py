"""Test script to verify the NEW Telegram session is valid."""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# New credentials
API_ID = 22413618
API_HASH = 'eed5d1903ea163db834735fcf91e3644'
SESSION_STRING = '1BVtsOLUBuy_B7oqPs-in09TF6gYiqRHtKoZU4-8jxTHQ-SVKnJDQTcuYEfN_Z2JmV0ejraqIb3YlTYgvXXcO5GhhGJbH6A8wQu8_7O2qocRBFeb_Qwnd5HdML7flNPY11-rDaPpmdTjCJSrPTO14IbeBPV_4UdkBQs8fgr97J2PfpYflWqpCQFxlVNn6he5H4RPJvBTwuDf7KlrC5SHZHSjMEcoSzC-DZTESlfsfajdOGVIWzWYANaGmTUcEZvptqW2VhrCeDZ1UqgC0Punp2e_r7Cz1g5pIAikM2R_XMJcxZiQo0pzTjBqC1i4ZYL-QmYCA-VQKO1GWTobFGZ51Oyrh5olTXqY='
GROUP_ID = -1002964079687


async def test_session():
    """Test if the Telegram session is valid and authorized."""
    print("=" * 60)
    print("Testing NEW Telegram Session")
    print("=" * 60)
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
        print("\n" + "=" * 60)
        print("[OK] All checks passed - session is VALID!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_session())
    exit(0 if result else 1)
