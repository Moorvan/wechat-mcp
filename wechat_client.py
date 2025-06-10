import httpx
from pydantic import BaseModel
import asyncio
from typing import Optional, TypeVar, Callable, Coroutine, Any, List
import os
from loguru import logger

# 日志文件路径
LOG_DIR = os.path.join(os.path.dirname(__file__), '.logs')
LOG_FILE = os.path.join(LOG_DIR, 'wechat_client.log')

os.makedirs(LOG_DIR, exist_ok=True)
logger.add(LOG_FILE, rotation="1 MB", retention="7 days", encoding="utf-8", enqueue=True, backtrace=True,
           diagnose=True)


class Icon(BaseModel):
    path: Optional[str] = None

class Contact(BaseModel):
    icon: Icon
    title: Optional[str] = None
    subtitle: Optional[str] = None
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
    chatLogs: List[ChatLog]

class WeChatClient:
    def __init__(self, server_addr: str = "http://localhost:48065"):
        self.server_addr = server_addr
        self.async_client = httpx.AsyncClient()
        self.sync_client = httpx.Client()

    def _log_request(self, method: str, url: str, params: Optional[dict] = None, data: Optional[dict] = None):
        logger.info(f"Request: {method} {url}")
        if params:
            logger.debug(f"Params: {params}")
        if data:
            logger.debug(f"Data: {data}")

    def _log_response(self, response: httpx.Response):
        logger.info(f"Response Status: {response.status_code}")
        try:
            logger.debug(f"Response JSON: {response.json()}")
        except httpx.JSONDecodeError:
            logger.debug(f"Response Text: {response.text}")

    def get_chat_logs(self, user: str, count: int = 10) -> ChatLogResponse:
        url = f"{self.server_addr}/wechat/chatlog"
        params = {"userId": user, "count": count}
        self._log_request("GET", url, params=params)
        response = self.sync_client.get(url, params=params)
        self._log_response(response)
        response.raise_for_status() # Raise an exception for bad status codes
        return ChatLogResponse.model_validate(response.json())

    async def get_chat_logs_async(self, user: str, count: int = 10) -> ChatLogResponse:
        url = f"{self.server_addr}/wechat/chatlog"
        params = {"userId": user, "count": count}
        self._log_request("GET", url, params=params)
        response = await self.async_client.get(url, params=params)
        self._log_response(response)
        response.raise_for_status()
        return ChatLogResponse.model_validate(response.json())

    def get_all_contacts(self) -> List[Contact]:
        url = f"{self.server_addr}/wechat/allcontacts"
        self._log_request("GET", url)
        response = self.sync_client.get(url)
        self._log_response(response)
        response.raise_for_status()
        return [Contact.model_validate(contact) for contact in response.json()]

    async def get_all_contacts_async(self) -> List[Contact]:
        url = f"{self.server_addr}/wechat/allcontacts"
        self._log_request("GET", url)
        response = await self.async_client.get(url)
        self._log_response(response)
        response.raise_for_status()
        return [Contact.model_validate(contact) for contact in response.json()]

    def search_contacts(self, keyword: str) -> List[Contact]:
        url = f"{self.server_addr}/wechat/search"
        params = {"keyword": keyword}
        self._log_request("GET", url, params=params)
        response = self.sync_client.get(url, params=params)
        self._log_response(response)
        response.raise_for_status()
        # Adjust to new response structure
        return [Contact.model_validate(contact) for contact in response.json().get("items", [])]

    async def search_contacts_async(self, keyword: str) -> List[Contact]:
        url = f"{self.server_addr}/wechat/search"
        params = {"keyword": keyword}
        self._log_request("GET", url, params=params)
        response = await self.async_client.get(url, params=params)
        self._log_response(response)
        response.raise_for_status()
        # Adjust to new response structure
        return [Contact.model_validate(contact) for contact in response.json().get("items", [])]

    def send_message(self, user_id: str, message: str):
        url = f"{self.server_addr}/wechat/send"
        params = {"userId": user_id, "content": message}
        self._log_request("POST", url, params=params)
        response = self.sync_client.post(url, params=params)
        self._log_response(response)
        response.raise_for_status()
        return response.json()

    async def send_message_async(self, user_id: str, message: str):
        url = f"{self.server_addr}/wechat/send"
        params = {"userId": user_id, "content": message}
        self._log_request("POST", url, params=params)
        response = await self.async_client.post(url, params=params)
        self._log_response(response)
        response.raise_for_status()
        return response.json()

# For convenience, we can instantiate a default client
# Users of this module can import this instance or create their own.
client = WeChatClient()