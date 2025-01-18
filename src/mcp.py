from rich import print
import asyncio
from .lib import get_chat_logs, get_contacts, send_message
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeChat MCP")


def format_xml_element(tag: str, content: str, indent_level: int = 0) -> str:
    indent = "  " * indent_level
    return f"{indent}<{tag}>{content}</{tag}>"


def format_contact_xml(contact, indent_level: int = 1) -> str:
    indent = "  " * indent_level
    return "\n".join([
        f"{indent}<contact>",
        format_xml_element("id", contact.arg, indent_level + 1),
        format_xml_element("title", contact.title, indent_level + 1),
        format_xml_element("subtitle", contact.subtitle, indent_level + 1),
        format_xml_element("valid", contact.valid, indent_level + 1),
        f"{indent}</contact>"
    ])


def format_message_xml(log, indent_level: int = 1) -> str:
    indent = "  " * indent_level
    return "\n".join([
        f"{indent}<message>",
        format_xml_element("from", log.fromUser, indent_level + 1),
        format_xml_element("to", log.toUser, indent_level + 1),
        format_xml_element("content", log.content, indent_level + 1),
        format_xml_element("time", log.createTime, indent_level + 1),
        format_xml_element("is_self", str(log.isSentFromSelf).lower(), indent_level + 1),
        f"{indent}</message>"
    ])


@mcp.resource("allcontacts://all_contacts")
def all_contacts() -> str:
    """
    Get a table of all contacts.
    """
    res = get_contacts()
    return "\n".join([
        "<contacts>",
        *[format_contact_xml(contact) for contact in res],
        "</contacts>"
    ])


@mcp.resource("contact://{name}")
def contact(name: str) -> str:
    """
    Get a table of contacts that match the given name.
    """ 
    res = get_contacts()
    filtered_contacts = [c for c in res if 
        ((c.title or "") + (c.subtitle or "") + c.arg).lower().find(name.lower()) >= 0]
    return "\n".join([
        "<contacts>",
        *[format_contact_xml(contact) for contact in filtered_contacts],
        "</contacts>"
    ])

@mcp.tool()
def chat_logs(user_id: str, count: int = 10) -> str:
    """
    Get a table of chat logs for the given user.
    When calling this method, remember to use the user id and not the name, title, or subtitle.
    """
    res = get_chat_logs(user_id, count)
    return "\n".join([
        "<chat_logs>",
        *[format_message_xml(log) for log in res.chatLogs],
        "</chat_logs>"
    ])

@mcp.tool()
def send(user_id: str, message: str):
    """
    Send a message to a WeChat user.
    When calling this method, remember to use the user id and not the name, title, or subtitle.
    """
    res = send_message(user_id, message)
    return res

if __name__ == "__main__":
    mcp.run("stdio")
