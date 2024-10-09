import os

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_community.chat_models import GigaChat

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

API_USER = os.getenv('API_USER')
API_PASSWORD = os.getenv('API_PASSWORD')
GIGACHAT_CREDENTIALS = os.getenv('GIGACHAT_CREDENTIALS')


class AuthException(Exception):
    def __init__(self, description: str):
        self.name = description


@app.exception_handler(AuthException)
async def unicorn_exception_handler(request: Request, exc: AuthException):
    return JSONResponse(
        status_code=200,
        headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        content={'success': False}
    )


async def ask_gigachat(request):
    gigachat = GigaChat(
        model='GigaChat-Pro',
        base_url='https://gigachat.devices.sberbank.ru/api/v1',
        scope='GIGACHAT_API_CORP',
        credentials=GIGACHAT_CREDENTIALS,
        verify_ssl_certs=False,
        profanity_check=False,
        profanity=False
    )

    return gigachat.invoke(request).content


@app.post("/predict")
async def create_item(request: Request, response: Response):
    body = await request.json()
    content = await ask_gigachat(body['messages'])
    response.headers["Access-Control-Allow-Origin"] = "*"
    return {'role': 'assistant', 'content': content}


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
