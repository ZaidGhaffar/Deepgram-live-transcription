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





class TranscriptCollector:
    def __init__(self):
        self.reset()
        self.is_collecting = False

    def reset(self):
        self.transcript_parts = []
        self.is_collecting = False

    def add_part(self, part):
        self.transcript_parts.append(part)

    def get_full_transcript(self):
        return ' '.join(self.transcript_parts)

class DeepgramConnection:
    def __init__(self,wesocket:WebSocket):
        self.websocket = wesocket
        self.dg_connection = None
        self.transcript_collector = TranscriptCollector()
        
        config = DeepgramClientOptions(options={"keepalive":"true"})
        self.deepgram = DeepgramClient(DEEPGRAM_API_KEY,config)
        
#        self.loop = asyncio.get_event_loop()
        
        #self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        
    def on_message(self, self_, result, **kwargs):
        """Synchronous message handler for Deepgram"""
        try:
            logger.debug(f"Received result: {result}")
            transcript = result.channel.alternatives[0].transcript
            
            if not transcript.strip():
                return
            
            if not result.speech_final:
                # If not speech final, update the last part or add a new part
                if not self.transcript_collector.is_collecting:
                    self.transcript_collector.add_part(transcript)
                    self.transcript_collector.is_collecting = True
                else:
                    # Replace the last part with the new interim result
                    if self.transcript_collector.transcript_parts:
                        self.transcript_collector.transcript_parts[-1] = transcript
            else:
                # This is a final sentence
                if self.transcript_collector.is_collecting:
                    # Replace or add the final part
                    if self.transcript_collector.transcript_parts:
                        self.transcript_collector.transcript_parts[-1] = transcript
                    else:
                        self.transcript_collector.add_part(transcript)
                    
                    # Get and print the full sentence
                    full_sentence = self.transcript_collector.get_full_transcript()
                    print(f"speaker: {full_sentence}")
                    
                    # Reset for next sentence
                    self.transcript_collector.reset()
                
        except Exception as e:
            logger.error(f"Error in on_message: {e}")
            
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