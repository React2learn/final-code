from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

try:
    import auth
except ImportError:
    from backend import auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    payload = auth.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = auth.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = ""

class UserLogin(BaseModel):
    username: str
    password: str
import ollama
import chromadb
import re
import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_FILE = os.path.join(BASE_DIR, "complaint_history.json")

def save_complaint(data):
    
    history = get_all_complaints()
    history.append(data)
    with open(STORAGE_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_all_complaints():
    
    if not os.path.exists(STORAGE_FILE):
        return []
    with open(STORAGE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# ChromaDB setup
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="new_banking_complaints")

app = FastAPI(title="Banking Complaint Resolver", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/register", tags=["Auth"])
async def register(req: UserRegister, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can register new users.")
    if not req.username or not req.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    existing = auth.get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    success = auth.create_user(username=req.username, password_raw=req.password, email=req.email, role="admin")
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user")
    return {"status": "success", "message": "Admin user registered successfully"}

@app.post("/api/login", tags=["Auth"])
async def login(req: UserLogin):
    user = auth.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not auth.verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user.get("role", "user")
    }

@app.get("/api/users", tags=["Auth"])
async def list_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can view users.")
    return auth.get_all_users()

@app.delete("/api/users/{username}", tags=["Auth"])
async def delete_user(username: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete users.")
    if current_user.get("username") == username:
        raise HTTPException(status_code=400, detail="You cannot delete your own administrator account.")
    success = auth.delete_user_by_username(username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or deletion failed.")
    return {"status": "success", "message": f"User {username} deleted successfully"}

class QueryRequest(BaseModel):
    query: str

# Updated model to allow specifying a complaint_id for chat
class ChatRequest(BaseModel):
    query: str
    complaint_id: Optional[str] = None

SYSTEM_INSTRUCTIONS = """
Act as an IT expert and provide a well-structured incident resolution. 
You are strictly bound to the technical data provided. Do not invent commands, errors, or logs that are not present or logically tied to the incident description.
"""

@app.post("/api/resolve", tags=["Complaints"])
async def resolve(req: QueryRequest, current_user: dict = Depends(get_current_user)):
    try:
        complaint_match = re.search(r"\b\d+\b", req.query)
        if not complaint_match:
            raise HTTPException(status_code=400, detail="Please provide a Complaint ID.")

        complaint_id = complaint_match.group()
        results = collection.get(ids=[complaint_id])
        
        if not results["ids"]:
            raise HTTPException(status_code=404, detail=f"Complaint ID {complaint_id} not found.")

        case_text = results["documents"][0]
        case_meta = results["metadatas"][0]

        rag_prompt = f"""
        You are an AI assistant specializing in banking complaint analysis and resolution.
        Analyze the provided banking complaint details and generate a clear, comprehensive, and detailed resolution report.

        Incident Details:
        - Short Description: {req.query}
        - Complaint ID: {case_meta.get('Complaint ID', complaint_id)}
        - Description: {case_text}
        - Company: {case_meta.get('Company', 'Unknown')}
        - Product: {case_meta.get('Product', 'Unknown')} | Sub-product: {case_meta.get('Sub-product', 'Unknown')}
        - Issue: {case_meta.get('Issue', 'Unknown')} | Sub-issue: {case_meta.get('Sub-issue', 'Unknown')}
        - State: {case_meta.get('State', 'Unknown')} | ZIP: {case_meta.get('ZIP code', 'Unknown')}
        - Tags: {case_meta.get('Tags', 'Unknown')}
        - Consumer consent: {case_meta.get('Consumer consent provided?', 'Unknown')}
        - Submitted via: {case_meta.get('Submitted via', 'Unknown')}
        - Date received: {case_meta.get('Date received', 'Unknown')}
        - Date sent to company: {case_meta.get('Date sent to company', 'Unknown')}
        - Company response: {case_meta.get('Company response to consumer', 'Unknown')}
        - Company public response: {case_meta.get('Company public response', 'Unknown')}
        - Timely response: {case_meta.get('Timely response?', 'Unknown')}
        - Consumer disputed: {case_meta.get('Consumer disputed?', 'Unknown')}

        Provide a well-structured incident resolution with the following sections:
        **Incident Summary**, **Root Cause Analysis**, **Detailed Resolution Steps**, **Verification Process**, **Preventive Measures**.
        """

        response = ollama.generate(
            model='qwen2.5:3b',
            prompt=rag_prompt,
            system=SYSTEM_INSTRUCTIONS,
            options={'temperature': 0.1, 'top_p': 0.9}
        )

        new_entry = {
            "status": "success",
            "complaint_id": case_meta.get("Complaint ID", complaint_id),
            "query": req.query,
            "matched_company": case_meta.get('Company', 'Unknown'),
            "matched_product": case_meta.get('Product', 'Unknown'),
            "matched_sub_product": case_meta.get('Sub-product', 'Unknown'),
            "matched_issue": case_meta.get('Issue', 'Unknown'),
            "matched_sub_issue": case_meta.get('Sub-issue', 'Unknown'),
            "state": case_meta.get('State', 'Unknown'),
            "zip_code": case_meta.get('ZIP code', 'Unknown'),
            "tags": case_meta.get('Tags', 'Unknown'),
            "consumer_consent": case_meta.get('Consumer consent provided?', 'Unknown'),
            "consumer_disputed": case_meta.get('Consumer disputed?', 'Unknown'),
            "company_response": case_meta.get('Company response to consumer', 'Unknown'),
            "company_public_response": case_meta.get('Company public response', 'Unknown'),
            "timely_response": case_meta.get('Timely response?', 'Unknown'),
            "resolution_markdown": response['response'],
            "created_date": case_meta.get('Date received', None),
            "sent_to_company_date": case_meta.get('Date sent to company', None)
        }

        save_complaint(new_entry)
        return new_entry

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/last-resolution", tags=["Complaints"])
async def get_last_resolution(current_user: dict = Depends(get_current_user)):
    history = get_all_complaints()
    if not history:
        raise HTTPException(status_code=404, detail="No resolution yet.")
    return history[-1]

@app.get("/api/all-complaints", tags=["Dashboard"])
async def get_all_data(current_user: dict = Depends(get_current_user)):
    return get_all_complaints()

@app.post("/api/chat", tags=["Complaints"])
async def chat_with_data(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    # Determine if this is a request to resolve a new complaint (by ID or description)
    complaint_match = re.search(r"\b\d{5,}\b", req.query)
    is_new_complaint = False
    
    if complaint_match:
        is_new_complaint = True
    else:
        # Ask LLM to classify if it's a new complaint description or a question
        classification = ollama.generate(
            model='qwen2.5:3b',
            prompt=f"Is the following text a description of a banking complaint (e.g. detailing an issue with a bank, credit card, or account), or is it a question asking about an already resolved complaint (e.g. 'What was the date?', 'Did they refund it?')? \n\nText: '{req.query}'\n\nAnswer ONLY with 'COMPLAINT' or 'QUESTION'.",
            options={'temperature': 0.1, 'max_tokens': 10}
        )
        if 'COMPLAINT' in classification['response'].upper():
            is_new_complaint = True

    if is_new_complaint:
        if complaint_match:
            complaint_id = complaint_match.group()
            results = collection.get(ids=[complaint_id])
            if not results or not results.get("ids"):
                return {"resolution_markdown": f"Complaint ID {complaint_id} not found."}
            case_text = results["documents"][0]
            case_meta = results["metadatas"][0]
            cid = complaint_id
        else:
            # Semantic search to find the closest complaint
            results = collection.query(query_texts=[req.query], n_results=1)
            if not results or not results.get("ids") or not results["ids"][0]:
                return {"resolution_markdown": "Could not find a matching complaint in the database."}
            case_text = results["documents"][0][0]
            case_meta = results["metadatas"][0][0]
            cid = results["ids"][0][0]
            
        rag_prompt = f"""
        You are an AI assistant specializing in banking complaint analysis and resolution.
        Analyze the provided banking complaint details and generate a clear, comprehensive, and detailed resolution report.

        Incident Details:
        - Short Description: {req.query}
        - Complaint ID: {case_meta.get('Complaint ID', cid)}
        - Description: {case_text}
        - Company: {case_meta.get('Company', 'Unknown')}
        - Product: {case_meta.get('Product', 'Unknown')} | Sub-product: {case_meta.get('Sub-product', 'Unknown')}
        - Issue: {case_meta.get('Issue', 'Unknown')} | Sub-issue: {case_meta.get('Sub-issue', 'Unknown')}
        - State: {case_meta.get('State', 'Unknown')} | ZIP: {case_meta.get('ZIP code', 'Unknown')}
        - Tags: {case_meta.get('Tags', 'Unknown')}
        - Consumer consent: {case_meta.get('Consumer consent provided?', 'Unknown')}
        - Submitted via: {case_meta.get('Submitted via', 'Unknown')}
        - Date received: {case_meta.get('Date received', 'Unknown')}
        - Date sent to company: {case_meta.get('Date sent to company', 'Unknown')}
        - Company response: {case_meta.get('Company response to consumer', 'Unknown')}
        - Company public response: {case_meta.get('Company public response', 'Unknown')}
        - Timely response: {case_meta.get('Timely response?', 'Unknown')}
        - Consumer disputed: {case_meta.get('Consumer disputed?', 'Unknown')}

        Provide a well-structured incident resolution with the following sections:
        **Incident Summary**, **Root Cause Analysis**, **Detailed Resolution Steps**, **Verification Process**, **Preventive Measures**.
        """

        response = ollama.generate(
            model='qwen2.5:3b',
            prompt=rag_prompt,
            system=SYSTEM_INSTRUCTIONS,
            options={'temperature': 0.1, 'top_p': 0.9}
        )

        new_entry = {
            "status": "success",
            "complaint_id": case_meta.get("Complaint ID", cid),
            "query": req.query,
            "matched_company": case_meta.get('Company', 'Unknown'),
            "matched_product": case_meta.get('Product', 'Unknown'),
            "matched_sub_product": case_meta.get('Sub-product', 'Unknown'),
            "matched_issue": case_meta.get('Issue', 'Unknown'),
            "matched_sub_issue": case_meta.get('Sub-issue', 'Unknown'),
            "state": case_meta.get('State', 'Unknown'),
            "zip_code": case_meta.get('ZIP code', 'Unknown'),
            "tags": case_meta.get('Tags', 'Unknown'),
            "consumer_consent": case_meta.get('Consumer consent provided?', 'Unknown'),
            "consumer_disputed": case_meta.get('Consumer disputed?', 'Unknown'),
            "company_response": case_meta.get('Company response to consumer', 'Unknown'),
            "company_public_response": case_meta.get('Company public response', 'Unknown'),
            "timely_response": case_meta.get('Timely response?', 'Unknown'),
            "resolution_markdown": response['response'],
            "created_date": case_meta.get('Date received', None),
            "sent_to_company_date": case_meta.get('Date sent to company', None)
        }

        save_complaint(new_entry)
        return {"complaint_id": case_meta.get("Complaint ID", cid), "resolution_markdown": response['response']}

    # If not a new complaint, handle as a chat question about existing data
    history = get_all_complaints()
    if not history:
        raise HTTPException(status_code=400, detail="No data available to chat about. Please provide a complaint ID or description first.")
    
    if req.complaint_id:
        target_report = next((item for item in history if str(item.get("complaint_id")) == str(req.complaint_id)), None)
        if not target_report:
            raise HTTPException(status_code=404, detail=f"Complaint ID {req.complaint_id} not found.")
    else:
        target_report = history[-1]
    
    report_text = target_report.get("resolution_markdown", "No data.")
    created_date = target_report.get("created_date", "Unknown")
    sent_date = target_report.get("sent_to_company_date", "Unknown")

    full_context = f"""
    Incident Dates:
    - Date Received: {created_date}
    - Date Sent to Company: {sent_date}
    
    Resolution Report:
    {report_text}
    """
    
    response = ollama.generate(
        model='qwen2.5:3b',
        prompt=f"Context:\n{full_context}\n\nQuestion: {req.query}",
        system="You are a helpful assistant. Use the provided dates and resolution report to answer the user's question accurately.",
        options={'temperature': 0.2}
    )
    
    return {"complaint_id": target_report.get("complaint_id"), "resolution_markdown": response['response']}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

# uvicorn main:app --reload
# admin
# admin123