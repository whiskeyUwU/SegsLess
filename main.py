import sys
import asyncio
from PyQt6.QtWidgets import QApplication
import qasync
from gui import MainWindow
import logging
from client import DiscordClient
from audio import AudioHandler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    if hasattr(app, "aboutToQuit"):
        app.aboutToQuit.connect(
            lambda: close_future(future, loop)
        )

    # Initialize components
    audio_handler = AudioHandler()
    discord_client = DiscordClient(audio_handler)
    
    window = MainWindow(discord_client, audio_handler)
    window.show()
    
    try:
        await future
    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        if discord_client.vc:
            await discord_client.leave_channel()
        if not discord_client.is_closed():
            await discord_client.close()
        audio_handler.cleanup()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    with loop:
        try:
            loop.run_until_complete(main())
        except RuntimeError:
            pass
        finally:
             # Ensure pending tasks like client.close() get a chance to finish if main() exits abruptly
             try:
                 pending = asyncio.all_tasks(loop)
                 if pending:
                     loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
             except RuntimeError:
                 pass
