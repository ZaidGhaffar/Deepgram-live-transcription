from fastapi import FastAPI,Request,WebSocket,WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
import asyncio
from dotenv import load_dotenv
load_dotenv()
from transcription import DeepgramConnection


PATH_STATIC_FILES = r"C:\python\deepgram\project-2\app\Frontend\static"
PATH_TEMPLATES = r"C:\python\deepgram\project-2\app\Frontend\templates"


app = FastAPI()
app.mount("/static",StaticFiles(directory=PATH_STATIC_FILES),name="static")
templates = Jinja2Templates(directory=PATH_TEMPLATES)


@app.get("/")
async def main_page(request:Request):
    return templates.TemplateResponse("index.html",{'request':request})

@app.websocket("/ws")
async def handle_websocket_conn(websocket:WebSocket):
    await websocket.accept()
    deepgram_connection = DeepgramConnection(websocket)
    print("⚡ Connection Established!!! ")
    try:
        await deepgram_connection.inital()
        while True:
            data = await websocket.receive_bytes()
            try:
                await asyncio.get_event_loop().run_in_executor(None, deepgram_connection.send_audio, data)
            except WebSocketDisconnect:
                print("WebSocket Disconnected!!! ")
    except Exception as e:
        print("deepgram connection error over the options")


if __name__ =="__main__":
    uvicorn.run("main:app",port=9000,host="0.0.0.0",reload=True)
