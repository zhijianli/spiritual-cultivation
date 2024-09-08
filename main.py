from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import openai
import asyncio
import functools
import uvicorn
import json
from cmd_manager.cmd_manager import CmdManager

app = FastAPI()
cmd_manager = CmdManager()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/copy_generate")
def read_root():
    return FileResponse('copy_generate.html')

@app.get("/temp")
def read_root():
    return FileResponse('temp.html')

@app.get("/login")
def temp():
    return FileResponse('login.html')

@app.get("/column")
def temp():
    return FileResponse('column.html')

@app.get("/dialogue")
def temp():
    return FileResponse('dialogue.html')

@app.get("/buddhist_treasure")
def temp():
    return FileResponse('buddhist_treasure.html')

@app.get("/sangha")
def temp():
    return FileResponse('sangha.html')

@app.get("/answer_question")
def temp():
    return FileResponse('answer_question.html')


@app.get("/temple_qa")
def temp():
    return FileResponse('temple_qa.html')

@app.get("/scripture-knowledge")
def temp():
    return FileResponse('scripture-knowledge.html')

@app.get("/scripture-etiquette")
def temp():
    return FileResponse('scripture-etiquette.html')

@app.get("/buddhist-history")
def temp():
    return FileResponse('buddhist-history.html')

@app.get("/chat")
def temp():
    return FileResponse('chat.html')

@app.get("/test")
def test():
    return FileResponse('test.html')

openai.api_key = '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'

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # await websocket.accept()
    while True:
        try:
            # receive message
            data = await websocket.receive_text()
            data = json.loads(data)
            print('received message: ' + str(data))

            prompt = ""
            maxCharacters = data['maxCharacters']
            if maxCharacters and int(maxCharacters) > 0:
                prompt = data['inputValue'] + "，要求中文,字数在" + str(maxCharacters) + "个字"
            else:
                prompt = data['inputValue']

            characterName = data['characterName']

            req_data = {
                'cmd': 'query_text',
                'prompt': prompt,
                'characterName':characterName
            }
            # handle message
            response = await cmd_manager.perform(websocket, req_data)
        except WebSocketDisconnect as e:
            print(e)
            manager.disconnect(websocket)
            break
        except Exception as e:
            print(e)
            manager.disconnect(websocket)
            break

        if response is not None:
            response = json.dumps(response, ensure_ascii=False)
            await websocket.send_text(response)

    # try:
    #     while True:
    #         data = await websocket.receive_text()
    #         print('received message: ' + data)
    #         prompt = data + "，要求中文，返回结果包括'标题'和'内容'"
    #         session = [{'role': 'system', 'content': '你是一个文案写手.'}, {'role': 'user', 'content': prompt}]
    #         chat_model = 'gpt-3.5-turbo'
    #         response = await create_chat_completion(session, chat_model)
    #         chat_text = ''
    #         for chunk in response:
    #             chunk_message = chunk['choices'][0]['delta']  # extract the message
    #             if 'content' not in chunk_message:
    #                 continue
    #             chat_text += chunk_message['content']
    #             print(chat_text)
    #             await manager.send_message(chat_text, websocket)
    # except WebSocketDisconnect:
    #     manager.disconnect(websocket)

async def create_chat_completion(session, chat_model):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, functools.partial(openai.ChatCompletion.create,
                                                                  model=chat_model,
                                                                  messages=session,
                                                                  max_tokens=20,
                                                                  stream=True))
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7777)