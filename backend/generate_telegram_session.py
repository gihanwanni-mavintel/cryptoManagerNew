"""Generate Telegram session string for authentication."""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Your Telegram API credentials
API_ID = 22413618
API_HASH = 'eed5d1903ea163db834735fcf91e3644'
PHONE_NUMBER = '+94773519452'


async def generate_session():
    """Generate a new Telegram session string."""
    print("=" * 60)
    print("Telegram Session String Generator")
    print("=" * 60)
    print(f"\nAPI ID: {API_ID}")
    print(f"Phone: {PHONE_NUMBER}")
    print("\nThis will create a new session for your Telegram account.")
    print("You will receive a code via Telegram app to verify.")
    print("-" * 60)

    # Create client with empty session (will generate new one)
    client = TelegramClient(StringSession(), API_ID, API_HASH)

    try:
        await client.connect()
        print("\n[Step 1/4] Connected to Telegram")

        # Request login code
        if not await client.is_user_authorized():
            print(f"\n[Step 2/4] Sending login code to {PHONE_NUMBER}...")
            await client.send_code_request(PHONE_NUMBER)

            # Get code from user
            print("\n" + "=" * 60)
            print("CHECK YOUR TELEGRAM APP!")
            print("You should have received a login code.")
            print("=" * 60)
            code = input("\nEnter the code you received: ").strip()

            try:
                print("\n[Step 3/4] Verifying code...")
                await client.sign_in(PHONE_NUMBER, code)
            except Exception as e:
                if "Two-steps verification" in str(e) or "password" in str(e).lower():
                    # 2FA enabled
                    print("\n[!] Two-factor authentication is enabled on your account.")
                    password = input("Enter your 2FA password: ").strip()
                    await client.sign_in(password=password)
                else:
                    raise e

        print("\n[Step 4/4] Authentication successful!")

        # Get session string
        session_string = client.session.save()

        # Display results
        print("\n" + "=" * 60)
        print("SUCCESS! Your session string has been generated.")
        print("=" * 60)
        print("\nSession String:")
        print("-" * 60)
        print(session_string)
        print("-" * 60)

        # Get user info
        me = await client.get_me()
        print(f"\nLogged in as: {me.first_name} {me.last_name or ''}")
        print(f"Username: @{me.username}")
        print(f"Phone: {me.phone}")

        # Save to file
        output_file = "telegram_session_string.txt"
        with open(output_file, 'w') as f:
            f.write(f"# Telegram Session Information\n")
            f.write(f"# Generated for: {me.first_name} (@{me.username})\n")
            f.write(f"# Phone: {me.phone}\n")
            f.write(f"# API ID: {API_ID}\n\n")
            f.write(f"TELEGRAM_API_ID={API_ID}\n")
            f.write(f"TELEGRAM_API_HASH={API_HASH}\n")
            f.write(f"TELEGRAM_SESSION_STRING={session_string}\n")

        print(f"\n[OK] Session string saved to: {output_file}")
        print("\nYou can now copy this session string to your .env file.")
        print("\nIMPORTANT: Keep this session string secure!")
        print("Anyone with this string can access your Telegram account.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Failed to generate session: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n[OK] Disconnected from Telegram")


if __name__ == "__main__":
    print("\nStarting session generation...")
    print("Make sure you have access to your Telegram app to receive the code!\n")
    asyncio.run(generate_session())
