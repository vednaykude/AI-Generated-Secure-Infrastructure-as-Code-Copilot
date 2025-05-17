from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import hmac
import hashlib
import os
import json
from dotenv import load_dotenv

from .services.github_service import GithubService
from .services.security_review import SecurityReviewService
from .services.ai_service import AIService
from .config import Settings

load_dotenv()

app = FastAPI(
    title="Cloud Security AI Review Bot",
    description="AI-powered security review system for Infrastructure as Code",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = Settings()
github_service = GithubService(settings)
ai_service = AIService(settings)
security_review = SecurityReviewService(github_service, ai_service)

class WebhookPayload(BaseModel):
    action: str
    pull_request: Optional[Dict] = None
    repository: Optional[Dict] = None

async def verify_webhook_signature(request: Request):
    if not settings.github_webhook_secret:
        return True
    
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        raise HTTPException(status_code=401, detail="No signature provided")
    
    body = await request.body()
    expected_signature = 'sha256=' + hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True

@app.get("/")
async def root():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    payload: WebhookPayload,
    verified: bool = Depends(verify_webhook_signature)
):
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    if payload.action == "opened" or payload.action == "synchronize":
        if payload.pull_request:
            await security_review.review_pull_request(payload.pull_request)
            return {"status": "success", "message": "Security review initiated"}
    
    return {"status": "skipped", "message": "Event not relevant for security review"}

@app.get("/status/{pr_number}")
async def get_review_status(pr_number: int):
    status = await security_review.get_review_status(pr_number)
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 