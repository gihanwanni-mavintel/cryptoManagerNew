"""Telegram listener service using Telethon."""
import asyncio
from datetime import datetime
from typing import Optional, Callable
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.events import NewMessage
from loguru import logger

from app.config import settings


class TelegramListener:
    """
    Telegram listener that monitors a group/channel for trading signals.
    Uses Telethon with a session string for authentication.
    """
    
    def __init__(self, on_message_callback: Optional[Callable] = None):
        """
        Initialize Telegram listener.

        Args:
            on_message_callback: Async callback function to handle new messages.
                                 Receives (message_text, sender, timestamp) as args.
        """
        self.api_id = settings.telegram_api_id
        self.api_hash = settings.telegram_api_hash
        self.session_string = settings.telegram_session_string
        self.group_id = settings.telegram_group_id
        self.on_message_callback = on_message_callback
        self.client: Optional[TelegramClient] = None
        self.running = False
        self.processed_messages = set()  # Track processed message IDs to prevent duplicates
        
    async def start(self):
        """Start the Telegram client and begin listening."""
        if not self.session_string:
            logger.warning("No Telegram session string provided, listener disabled")
            return
            
        if not self.group_id:
            logger.warning("No Telegram group ID provided, listener disabled")
            return
        
        try:
            logger.info("Starting Telegram listener...")
            
            # Create client with session string
            self.client = TelegramClient(
                StringSession(self.session_string),
                self.api_id,
                self.api_hash
            )
            
            # Connect
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.error("Telegram session is not authorized")
                return
            
            # Get info about the monitored group
            try:
                entity = await self.client.get_entity(self.group_id)
                logger.info(f"Monitoring Telegram group: {getattr(entity, 'title', self.group_id)}")
            except Exception as e:
                logger.warning(f"Could not get group info: {e}")
            
            # Register message handler
            @self.client.on(NewMessage(chats=self.group_id))
            async def handle_new_message(event):
                await self._process_message(event)
            
            self.running = True
            logger.info("Telegram listener started successfully")
            
            # Keep running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Error starting Telegram listener: {e}")
            self.running = False
    
    async def _process_message(self, event):
        """Process incoming message from Telegram."""
        try:
            message = event.message
            text = message.text or ""

            # Skip empty messages
            if not text.strip():
                return

            # Check for duplicate messages using message ID
            message_id = message.id
            if message_id in self.processed_messages:
                logger.debug(f"Skipping duplicate message ID: {message_id}")
                return

            # Mark message as processed
            self.processed_messages.add(message_id)

            # Keep only last 1000 message IDs to prevent memory growth
            if len(self.processed_messages) > 1000:
                # Remove oldest half
                self.processed_messages = set(list(self.processed_messages)[-500:])

            # Get sender info
            sender = "TELEGRAM"
            if message.sender:
                sender = getattr(message.sender, 'username', None) or \
                         getattr(message.sender, 'first_name', 'Unknown')

            timestamp = message.date

            logger.info(f"New Telegram message from {sender}: {text[:100]}...")

            # Call the callback if provided
            if self.on_message_callback:
                try:
                    await self.on_message_callback(text, sender, timestamp)
                except Exception as e:
                    logger.error(f"Error in message callback: {e}")

        except Exception as e:
            logger.error(f"Error processing Telegram message: {e}")
    
    async def stop(self):
        """Stop the Telegram listener."""
        self.running = False
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram listener stopped")
    
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self.running


class TelegramSignalProcessor:
    """
    Processor that integrates Telegram listener with trade execution.
    """
    
    def __init__(self, db_session_factory):
        """
        Initialize signal processor.
        
        Args:
            db_session_factory: Function that returns a database session
        """
        self.db_session_factory = db_session_factory
        self.listener = TelegramListener(on_message_callback=self._handle_signal)
        
    async def _handle_signal(self, text: str, sender: str, timestamp: datetime):
        """
        Handle incoming signal from Telegram.
        
        Args:
            text: Message text
            sender: Sender username/name
            timestamp: Message timestamp
        """
        from app.services.telegram_parser import TelegramParser
        from app.services.trade_service import TradeService
        
        # Check if message looks like a signal (has hashtag with pair)
        if '#' not in text:
            logger.debug("Message doesn't contain hashtag, skipping")
            return
        
        # Parse the signal
        parser = TelegramParser()
        parsed = parser.parse_message(text)

        if not parsed:
            logger.debug("Could not parse signal from message")
            return

        logger.info(f"Parsed signal: {parsed.pair} {parsed.setup_type} @ {parsed.entry}")
        
        # Process with trade service
        db = self.db_session_factory()
        try:
            from app.models.schemas import TelegramMessageInput

            trade_service = TradeService(db)
            message_input = TelegramMessageInput(
                text=text,
                sender=sender,
                channel="Telegram Auto"
            )
            result = trade_service.process_telegram_message(
                message_input=message_input,
                user_id=1,
                auto_execute=settings.auto_execute_trades
            )
            
            if result["success"]:
                logger.info(f"Signal processed successfully: {result['message']}")
            else:
                logger.warning(f"Signal processing failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
        finally:
            db.close()
    
    async def start(self):
        """Start the signal processor."""
        await self.listener.start()
    
    async def stop(self):
        """Stop the signal processor."""
        await self.listener.stop()


# Standalone runner for testing
async def run_listener():
    """Run the Telegram listener standalone."""
    from app.database import SessionLocal
    
    processor = TelegramSignalProcessor(db_session_factory=SessionLocal)
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(run_listener())
