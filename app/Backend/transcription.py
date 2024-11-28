from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveTranscriptionEvents
)
from dotenv import load_dotenv
load_dotenv()
import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastapi import WebSocket

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")




class DeepgramConnection:
    def __init__(self,wesocket:WebSocket):
        self.websocket = wesocket
        self.dg_connection = None
        
        config = DeepgramClientOptions(options={"keepalive":"true"})
        self.deepgram = DeepgramClient(DEEPGRAM_API_KEY,config)
        
#        self.loop = asyncio.get_event_loop()
        
        #self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        
    def on_message(self, self_, result, **kwargs):
        """Synchronous message handler for Deepgram"""
        try:
            transcript = result.channel.alternatives[0].transcript
            if transcript:
                if len(transcript) == 0:
                   return
                print(f"Transcription:    {transcript}")
                logger.info(f"Transcription: {transcript}")
                    
            else:
                #logger.warning(f"Unexpected result format: {result}")
                print("Transcription is empty")
        except Exception as e:
            logger.error(f"Error in on_message: in transcription")
            
    def on_error(self, self_, error, **kwargs):
        logger.error(f"Deepgram error: {error}")
        
    def on_close(self, self_, close, **kwargs):
        logger.info(f"Deepgram connection closed: {close}")
        
    async def inital(self):
        self.dg_connection = self.deepgram.listen.live.v('1')
        
        # Register event handlers
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        self.dg_connection.on(LiveTranscriptionEvents.Error, self.on_error)
        self.dg_connection.on(LiveTranscriptionEvents.Close, self.on_close)
            
        options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000
            )
        try:
            self.dg_connection.start(options)
            print("Deepgram Websocket connection has been fully connected!!! now you can proceed")
        except Exception as e:
            print("getting error on setting up these options of deepgram")
    
    def send_audio(self,data):
        try:
            if self.dg_connection:
                self.dg_connection.send(data)
        except Exception as e:
            print(f"can't sent data to the deegram socket due to following errors:     {e}")
            
    def close(self):
        """Close the Deepgram connection (synchronous method)"""
        try:
            if self.dg_connection:
                self.dg_connection.finish()
                self.dg_connection = None
        except Exception as e:
            logger.error(f"Error closing Deepgram: {e}")