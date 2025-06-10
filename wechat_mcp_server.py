from mcp.server.fastmcp import FastMCP
from rich import print
import asyncio
from wechat_client import get_chat_logs, get_contacts, send_message
import unicodedata
import urllib.parse # <--- 添加这一行

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
    # Explicitly URL-decode the name parameter
    decoded_name = urllib.parse.unquote(name) # <--- 添加解码步骤

    # We normalize and casefold for robust Unicode-aware searching.
    res = get_contacts()
    
    # Normalize the search name, handle if name is None or empty
    normalized_search_name = normalize_caseless(decoded_name or "") # <--- 使用解码后的名字
    # print(f"Decoded name: '{decoded_name}', Normalized search name: '{normalized_search_name}' from input: '{name}'")

    if not normalized_search_name: # If search name is empty, return no contacts
        return "\n".join([
            "<contacts>",
            "</contacts>"
        ])

    filtered_contacts = []
    for c in res:
        # Concatenate relevant contact fields for searching, ensuring parts are strings
        contact_full_string = f"{c.title or ''} {c.subtitle or ''} {c.arg or ''}"
        # contact_full_string = (c.title or "") + (c.subtitle or "") + (c.arg or "")
        normalized_contact_string = normalize_caseless(contact_full_string)
        
        if normalized_contact_string.find(normalized_search_name) >= 0:
            filtered_contacts.append(c)
            
    return "\n".join([
        "<contacts>",
        *[format_contact_xml(contact) for contact in filtered_contacts],
        "</contacts>"
    ])

@mcp.tool()
def chat_logs(user_id: str, count: int = 10) -> str:
    """
    获取指定用户的聊天记录。返回的聊天记录内容以及后续基于这些内容的分析和输出都应为中文。
    调用此方法时，请确保使用用户 ID，而不是名称、标题或子标题。
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
    向微信用户发送消息。发送的消息内容应为中文。
    调用此方法时，请确保使用用户 ID，而不是名称、标题或子标题。
    """
    res = send_message(user_id, message)
    return res


if __name__ == "__main__":
    mcp.run("stdio")
