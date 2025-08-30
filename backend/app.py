import numpy as np
import databases
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from utils import perform_ocr

from chat import get_llm_response


import uuid

# Database configuration
# DATABASE URL: postgresql://username:password@host:port/database_name
DATABASE_URL = "postgresql://postgres:example@db:5432/postgres"
database = databases.Database(DATABASE_URL)

class ChatRequest(BaseModel):
    message: str
    model: str
    session_id: Optional[str] = None
    username: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Ok"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/ocr")
async def ocr_receipt(file: UploadFile, username: str = Form("default")):
    # Check if the uploaded file is an image
    if file.content_type.startswith("image"):
        image_bytes = await file.read()
        img_array = np.frombuffer(image_bytes, np.uint8)

        ocr_text = perform_ocr(img_array)
        
        # Check if user exists, create if not
        user_check = await database.fetch_one(
            "SELECT user_id FROM users WHERE username = :username",
            {"username": username}
        )
        if not user_check:
            await database.execute(
                "INSERT INTO users (username) VALUES (:username)",
                {"username": username}
            )
            # Get the newly created user_id
            user_record = await database.fetch_one(
                "SELECT user_id FROM users WHERE username = :username",
                {"username": username}
            )
            db_user_id = user_record["user_id"]
        else:
            db_user_id = user_check["user_id"]
        
        # Store receipt in database
        await database.execute(
            "INSERT INTO receipt (user_id, receipt_text) VALUES (:user_id, :receipt_text)",
            {"user_id": db_user_id, "receipt_text": ocr_text}
        )
        
        return JSONResponse(content={"result": ocr_text}, status_code=200)
    else:
        return {"error": "Uploaded file is not an image"}

@app.post("/chat", response_model= ChatResponse)
async def chat(request: ChatRequest):
    # Set default username if not provided
    username = request.username if request.username else "default"
    
    # Check if user exists, create if not
    user_check = await database.fetch_one(
        "SELECT user_id FROM users WHERE username = :username",
        {"username": username}
    )
    if not user_check:
        await database.execute(
            "INSERT INTO users (username) VALUES (:username)",
            {"username": username}
        )
        # Get the newly created user_id
        user_record = await database.fetch_one(
            "SELECT user_id FROM users WHERE username = :username",
            {"username": username}
        )
        user_id = user_record["user_id"]
    else:
        user_id = user_check["user_id"]
    
    if request.session_id:
        # Check if session exists in database
        session_check = await database.fetch_one(
            "SELECT session_id FROM sessions WHERE session_id = :session_id",
            {"session_id": request.session_id}
        )
        if session_check:
            session_id = request.session_id
        else:
            # Session ID provided but not found, create new session
            session_id = str(uuid.uuid4())
            await database.execute(
                "INSERT INTO sessions (session_id, user_id) VALUES (:session_id, :user_id)",
                {"session_id": session_id, "user_id": user_id}
            )
    else:
        # No session ID provided, create new session
        session_id = str(uuid.uuid4())
        await database.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (:session_id, :user_id)",
            {"session_id": session_id, "user_id": user_id}
        )

    llm_output = await get_llm_response(
        message=request.message, 
        model=request.model,
        session_id=session_id,
        user_id=user_id,
        database=database
    )

    messages_query = """
        INSERT INTO messages (session_id, sender, message_text)
        VALUES (:session_id, :sender, :message_text)
        """
    await database.execute(query=messages_query, values={"session_id": session_id, "sender": "User", "message_text": request.message})
    await database.execute(query=messages_query, values={"session_id": session_id, "sender": "AI", "message_text": llm_output})

    return ChatResponse(response=llm_output, session_id=session_id)


## db
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()