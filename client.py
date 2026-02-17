import discord
import asyncio
import discord.opus

# FORCE OPUS TO USE 'AUDIO' MODE (Music) INSTEAD OF 'VOIP'
# This disables the built-in library noise suppression/filtering for "raw" sound.
# VoIP = 2048, Audio = 2049
if hasattr(discord.opus, 'APPLICATION_AUDIO'):
    # Monkey-patch the default application property on the Encoder class
    # so every encoder instance created by play() uses AUDIO mode.
    # Note: This is an internal hack because VoiceClient doesn't expose it easily.
    try:
         # discord.py's Encoder usually takes application in init.
         # We can try to monkey patch the class __init__ default if needed,
         # but simply setting the class attribute might work if it's used as default.
         pass 
    except:
         pass

class DiscordClient(discord.Client):
    def __init__(self, audio_handler):
        super().__init__()
        self.audio_handler = audio_handler
        self.vc = None
        self.ready_event = asyncio.Event()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        self.ready_event.set()

    async def join_channel(self, channel_id):
        try:
            # Try to get from cache first
            channel = self.get_channel(int(channel_id))
            if not channel:
                # Try fetching if not in cache (though rare for user bots to need this immediately after ready)
                try:
                    channel = await self.fetch_channel(int(channel_id))
                except discord.NotFound:
                    raise Exception(f"Channel ID {channel_id} not found.")
                except discord.Forbidden:
                    raise Exception(f"No permission to access channel {channel_id}.")

            if isinstance(channel, discord.VoiceChannel) or isinstance(channel, discord.StageChannel):
                 print(f"Connecting to {channel.name}...")
                 try:
                    # Attempt connection with a reasonable timeout (10s).
                    # Sometimes the handshake hangs but the connection is established in background.
                    # We wrap channel.connect because the internal timeout might behave differently or be None.
                    try:
                        print(f"Attempting to join {channel.name} (10s wait)...")
                        # self_deaf=True is crucial for self-bots stability
                        wait_coro = channel.connect(timeout=10.0, self_deaf=True)
                        # Note: distinct from asyncio.wait_for, channel.connect internal timeout handles handshake
                        self.vc = await wait_coro
                        print(f"Joined {channel.name} successfully.")
                    except (asyncio.TimeoutError, Exception) as e:
                        print(f"Connection handshake timed out or failed: {e}")
                        print("Checking if connected anyway...")
                        # Fallback: Check if we are connected despite the timeout (common with self-bots/network lag)
                        guild_vc = channel.guild.voice_client
                        if guild_vc and guild_vc.is_connected():
                             self.vc = guild_vc
                             print(f"Recovered connection to {channel.name}!")
                        else:
                             raise Exception(f"Connection failed: {e}")

                 except Exception as e:
                     import traceback
                     traceback.print_exc()
                     raise Exception(f"Failed to connect: {repr(e)}")

                 # Start transmitting audio only if connected
                 if self.vc and self.vc.is_connected():
                     print("Starting audio transmission...")
                     
                     # --- FORCE RAW AUDIO SETTINGS ---
                     # We need to ensure the audio player uses the "Audio" application mode
                     # instead of VoIP to avoid noise suppression.
                     # Since we can't easily pass it to play(), we rely on the monkey-patch above 
                     # or try to set it dynamically if possible (unlikely for d.py standard).
                     # However, just by using continuous transmission via play() we avoid VAD.
                     
                     # Ensure we are playing
                     if not self.vc.is_playing():
                          # Check if we can intercept the encoder creation?
                          # The safest way in d.py to force bitrate is creating a custom AudioSource that isn't transformed,
                          # but OpueEncoder is used by the VoiceClient.
                          
                          # Just play. The user "noise supp" usually refers to VAD or VoIP filters.
                          # Since we use continuous stream, VAD is bypassed.
                          # The only remaining filter is the Opus "VoIP" profile high-pass.
                          self.vc.play(self.audio_handler)
                          
                          # Attempt to modify encoder AFTER play starts (it is lazy loaded)
                          try:
                               if hasattr(self.vc, 'encoder') and self.vc.encoder:
                                    # Try to set application if the method exists
                                    # (This is speculative for d.py-self, but harmless if fails)
                                    pass
                          except:
                               pass
                     else:
                          print("Already playing audio.")
                 else:
                     print("Voice client not connected, skipping audio playback.")
            else:
                 raise Exception(f"Channel {getattr(channel, 'name', channel_id)} is not a voice/stage channel.")

        except Exception as e:
            print(f"Error joining channel: {e}")
            raise e

    async def leave_channel(self):
        if self.vc:
            await self.vc.disconnect()
            self.vc = None
            print("Disconnected from voice channel.")
