from mcp.server.fastmcp import FastMCP
from rich import print
import asyncio
from wechat_client import client # Import the client instance
import unicodedata
import urllib.parse
from datetime import datetime

mcp = FastMCP("WeChat MCP")

# Contact cache
contact_cache = {}

async def get_contact_name_with_cache(wxid: str) -> str:
    """Gets contact name from cache or fetches and caches it."""
    if wxid in contact_cache:
        return contact_cache[wxid]
    
    # wxid_ 开头的通常是个人用户，直接查询
    # 非 wxid_ 开头的可能是群聊，也可能是其他类型的id，尝试查询
    # 如果查询不到，或者wxid本身就是显示名称（例如某些系统消息），则返回原始wxid
    if not wxid: # Handle empty wxid if necessary
        return "Unknown"
        
    try:
        contacts = await client.search_contacts_async(keyword=wxid)
        if contacts:
            contact_name = contacts[0].title
            contact_cache[wxid] = contact_name
            return contact_name
    except Exception as e:
        print(f"Error fetching contact for {wxid}: {e}")
    
    # Fallback to original wxid if not found or error
    contact_cache[wxid] = wxid # Cache the wxid itself to avoid repeated failed lookups
    return wxid

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


async def format_message_xml(log, indent_level: int = 1) -> str:
    indent = "  " * indent_level

    # Convert timestamp to readable format
    try:
        readable_time = datetime.fromtimestamp(int(log.createTime)).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        readable_time = log.createTime # Fallback to original if conversion fails

    content_to_display = log.content
    from_user_display_name = log.fromUser # Default to original wxid

    # Handle group messages and actual sender
    if not log.fromUser.startswith("wxid_") and "wxid_" in log.content: # Likely a group chat
        group_name = await get_contact_name_with_cache(log.fromUser)
        try:
            parts = log.content.split(":", 1)
            if len(parts) > 1 and parts[0].strip().startswith("wxid_"):
                actual_sender_id = parts[0].strip()
                actual_sender_name = await get_contact_name_with_cache(actual_sender_id)
                
                if actual_sender_name != actual_sender_id: # Successfully resolved actual sender's name
                    from_user_display_name = actual_sender_name
                    content_to_display = parts[1].strip()
                else: # Couldn't resolve actual sender's name, show group (sender_id)
                    from_user_display_name = f"{group_name} ({actual_sender_id})"
                    content_to_display = parts[1].strip() # Still remove prefix
            else:
                # No clear wxid_ prefix in content, use group name
                from_user_display_name = group_name
        except Exception as e:
            print(f"Error processing group message sender for {log.fromUser}: {e}")
            from_user_display_name = await get_contact_name_with_cache(log.fromUser) # Fallback to group name
    else:
        # Direct message or system message, resolve fromUser
        from_user_display_name = await get_contact_name_with_cache(log.fromUser)

    to_user_display_name = await get_contact_name_with_cache(log.toUser)


    return "\n".join([
        f"{indent}<message>",
        format_xml_element("from", from_user_display_name, indent_level + 1),
        format_xml_element("to", to_user_display_name, indent_level + 1),
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
async def contact(name: str) -> str:
    """
    获取匹配指定名称的联系人列表。
    """
    decoded_name = urllib.parse.unquote(name)
    normalized_search_name = normalize_caseless(decoded_name or "")

    if not normalized_search_name:
        res = []
    else:
        res = await client.search_contacts_async(keyword=decoded_name)

    res_to_format = res
            
    return "\n".join([
        "<contacts>",
        *[format_contact_xml(contact) for contact in res_to_format],
        "</contacts>"
    ])

@mcp.tool()
async def chat_logs(user_id: str, count: int = 10) -> str:
    """
    获取指定用户的聊天记录。返回的聊天记录内容以及后续基于这些内容的分析和输出都应为中文。
    调用此方法时，请确保使用用户 ID，而不是名称、标题或子标题。
    """
    res = await client.get_chat_logs_async(user_id, count) # Use client.get_chat_logs_async
    return "\n".join([
        "<chat_logs>",
        *[await format_message_xml(log) for log in res.chatLogs],
        "</chat_logs>"
    ])

@mcp.tool()
async def send(user_id: str, message: str):
    """
    向微信用户发送消息。发送的消息内容应为中文。
    调用此方法时，请确保使用用户 ID，而不是名称、标题或子标题。
    """
    res = await client.send_message_async(user_id, message) # Use client.send_message_async
    return res



if __name__ == "__main__":
    mcp.run("stdio")
