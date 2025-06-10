from mcp.server.fastmcp import FastMCP
from rich import print
import asyncio
from wechat_client import client # Import the client instance
import unicodedata
import urllib.parse
from datetime import datetime

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

    # Convert timestamp to readable format
    try:
        readable_time = datetime.fromtimestamp(int(log.createTime)).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        readable_time = log.createTime # Fallback to original if conversion fails

    # Get contact names for fromUser and toUser
    from_user_name = log.fromUser
    to_user_name = log.toUser
    actual_sender_id_in_content = None
    content_to_display = log.content

    # Check if it's a group message and extract actual sender if possible
    if not log.fromUser.startswith("wxid_") and "wxid_" in log.content:
        try:
            # Extract the wxid from the content (e.g., "wxid_xxxx: message content")
            parts = log.content.split(":", 1)
            if len(parts) > 1 and "wxid_" in parts[0]:
                actual_sender_id_in_content = parts[0].strip()
                # Attempt to get the actual sender's name
                sender_contacts = client.search_contacts(keyword=actual_sender_id_in_content)
                if sender_contacts:
                    from_user_name = sender_contacts[0].title # Use actual sender's name
                    content_to_display = parts[1].strip() if len(parts) > 1 else log.content # Remove wxid from content
                else:
                    # If actual sender not found by wxid, keep group name but note the wxid
                    from_user_name = f"{log.fromUser} ({actual_sender_id_in_content})"
                    # Optionally, still remove the prefix if it's clearly a prefix
                    content_to_display = parts[1].strip() if len(parts) > 1 else log.content
            # If wxid is not at the beginning, don't change from_user_name for now
            # and rely on the general fromUser lookup below.
        except Exception as e:
            print(f"Error processing group message sender: {e}")
            # Fallback to group name if an error occurs
            from_user_name = log.fromUser
    else:
        # For non-group messages or if no actual sender in content, try to resolve fromUser directly
        try:
            from_contacts = client.search_contacts(keyword=log.fromUser)
            if from_contacts:
                from_user_name = from_contacts[0].title
        except Exception as e:
            print(f"Error fetching from_user contact: {e}") # Log error, keep original wxid

    # Resolve toUser (recipient)
    try:
        to_contacts = client.search_contacts(keyword=log.toUser)
        if to_contacts:
            to_user_name = to_contacts[0].title
    except Exception as e:
        print(f"Error fetching to_user contact: {e}") # Log error, keep original wxid

    return "\n".join([
        f"{indent}<message>",
        format_xml_element("from", from_user_name, indent_level + 1),
        format_xml_element("to", to_user_name, indent_level + 1),
        format_xml_element("content", content_to_display, indent_level + 1),
        format_xml_element("time", readable_time, indent_level + 1),
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

