# Library for interacting with WeChat API
from httpx import AsyncClient
import httpx
from pydantic import BaseModel
import asyncio
from typing import Optional, TypeVar, Callable, Coroutine, Any

SERVER_ADDR = "http://localhost:48065"
async_client = AsyncClient()
sync_client = httpx.Client()

T = TypeVar('T')

def run_async_function(func: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs) -> T:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(func(*args, **kwargs))

class Icon(BaseModel):
    path: str | None

class Contact(BaseModel):
    icon: Icon
    title: Optional[str]
    subtitle: Optional[str]
    arg: str
    valid: int


class ChatLog(BaseModel):
    fromUser: str
    toUser: str
    content: str
    createTime: int
    isSentFromSelf: bool


class ChatLogResponse(BaseModel):
    hasMore: int
    chatLogs: list[ChatLog]


def get_chat_logs(user: str, count: int = 10) -> ChatLogResponse:
    response = sync_client.get(f"{SERVER_ADDR}/wechat/chatlog", params={"userId": user, "count": count})
    return ChatLogResponse.model_validate(response.json())


async def get_chat_logs_async(user: str, count: int = 10) -> ChatLogResponse:
    response = await async_client.get(f"{SERVER_ADDR}/wechat/chatlog", params={"userId": user, "count": count})
    return ChatLogResponse.model_validate(response.json())


def get_contacts() -> list[Contact]:
    response = sync_client.get(f"{SERVER_ADDR}/wechat/allcontacts")
    return [Contact.model_validate(contact) for contact in response.json()]


async def get_contacts_async() -> list[Contact]:
    response = await async_client.get(f"{SERVER_ADDR}/wechat/allcontacts")
    return [Contact.model_validate(contact) for contact in response.json()]


def send_message(user_id: str, message: str):
    response = sync_client.post(f"{SERVER_ADDR}/wechat/send", params={"userId": user_id, "content": message})
    return response.json()


async def send_message_async(user_id: str, message: str):
    response = await async_client.post(f"{SERVER_ADDR}/wechat/send", params={"userId": user_id, "content": message})
    return response.json()