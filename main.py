import os
import secrets
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from langchain_community.chat_models import GigaChat

app = FastAPI()
security = HTTPBasic()

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
        content={'success': False}
    )


def get_current_username(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = bytes(API_USER, 'utf-8')
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = bytes(API_PASSWORD, 'utf-8')
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise AuthException(
            description='Incorrect username or password'
        )
    return credentials.username


async def ask_gigachat(request):
    gigachat = GigaChat(
        model='GigaChat-Pro',
        base_url='https://gigachat.devices.sberbank.ru/api/v1',
        scope='GIGACHAT_API_CORP',
        credentials=GIGACHAT_CREDENTIALS,
        verify_ssl_certs=False,
        profanity_check=False,
    )

    return gigachat.invoke(request).content


@app.get("/auth")
async def auth(username: Annotated[str, Depends(get_current_username)]):
    return {'success': True}


@app.post("/predict")
async def create_item(request: Request, username: Annotated[str, Depends(get_current_username)]):
    body = await request.json()
    content = await ask_gigachat(body['messages'])
    return {'role': 'assistant', 'content': content}


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
