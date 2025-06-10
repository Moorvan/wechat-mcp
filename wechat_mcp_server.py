from mcp.server.fastmcp import FastMCP
from rich import print
import asyncio
from wechat_client import client # Import the client instance
import unicodedata
import urllib.parse

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


# Helper function for Unicode normalization and casefolding
def normalize_caseless(text: str) -> str:
    """Normalizes and casefolds a string for robust comparison."""
    # NFKC performs compatibility decomposition, followed by canonical composition.
    # casefold() is a more aggressive version of lower() for caseless matching.
    return unicodedata.normalize('NFKC', text).casefold()


@mcp.tool()
def contact(name: str) -> str:
    """
    获取匹配指定名称的联系人列表。
    """
    decoded_name = urllib.parse.unquote(name)
    normalized_search_name = normalize_caseless(decoded_name or "")

    if not normalized_search_name:
        res = []
    else:
        res = client.search_contacts(keyword=decoded_name)

    res_to_format = res
            
    return "\n".join([
        "<contacts>",
        *[format_contact_xml(contact) for contact in res_to_format],
        "</contacts>"
    ])

@mcp.tool()
def chat_logs(user_id: str, count: int = 10) -> str:
    """
    获取指定用户的聊天记录。返回的聊天记录内容以及后续基于这些内容的分析和输出都应为中文。
    调用此方法时，请确保使用用户 ID，而不是名称、标题或子标题。
    """
    res = client.get_chat_logs(user_id, count) # Use client.get_chat_logs
    return "\n".join([
        "<chat_logs>",
        *[format_message_xml(log) for log in res.chatLogs],
        "</chat_logs>"
    ])

@mcp.tool()
def send(user_id: str, message: str):
    """
    向微信用户发送消息。发送的消息内容应为中文。
    调用此方法时，请确保使用用户 ID，而不是名称、标题或子标题。
    """
    res = client.send_message(user_id, message) # Use client.send_message
    return res


if __name__ == "__main__":
    mcp.run("stdio")

