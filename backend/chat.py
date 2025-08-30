from openai import OpenAI
from prompts import SYSTEM_PROMPT, USER_PROMPT
import os
import databases

async def receipt_history(user_id: str, database: databases.Database) -> str:
    """Fetch all receipt text for a given user_id from database"""
    query = "SELECT receipt_text, created_at FROM receipt WHERE user_id = :user_id ORDER BY created_at DESC"
    receipts = await database.fetch_all(query, {"user_id": user_id})
    
    if not receipts:
        return "No receipt history found."
    
    history = []
    for receipt in receipts:
        history.append(f"Receipt: {receipt['receipt_text']}")
    
    return "\n\n".join(history)

async def conversation_history(session_id: str, database: databases.Database) -> str:
    """Fetch and format conversation history for a given session_id"""
    query = """
        SELECT sender, message_text FROM messages
        WHERE session_id = :session_id
        ORDER BY created_at DESC
        LIMIT 5
        """
    conversation_records = await database.fetch_all(query=query, values={"session_id": session_id})
    
    if conversation_records:
        formatted_conversations = []
        for record in conversation_records:
            formatted_conversations.append(f"{record['sender']}: {record['message_text']}")
        return "\n".join(formatted_conversations)
    else:
        return "No previous conversation history."

async def get_llm_response(message: str, model: str, session_id: str, user_id: str, database: databases.Database):
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Get conversation history and receipt history
    user_conversation_history = await conversation_history(session_id, database)
    user_receipt_history = await receipt_history(user_id, database)
    
    # Create the system prompt
    system_prompt = SYSTEM_PROMPT.replace("{receipt_history}", user_receipt_history).replace("{conversation_history}", user_conversation_history)

    response = client.chat.completions.create(
        model=model,
        temperature=0.01,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": USER_PROMPT.replace("{message}", message)
            },
        ],
    )

    return response.choices[0].message.content
    

