from rich import print
import asyncio
from .lib import get_chat_logs, get_contacts, send_message

def main():
    res = send_message(input("user_id: "), "Hello, world")
    print(res)

if __name__ == "__main__":
    main()
