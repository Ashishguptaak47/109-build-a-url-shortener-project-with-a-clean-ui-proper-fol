from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from app.config import BASE_URL
from app.database import init_db
from app.shortener import generate_code, validate_url, validate_custom_code
from app import repository

app = FastAPI(title="SnipURL Shortener", version="1.0.0")
templates_dir = Path(__file__).resolve().parent / "app" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@app.on_event("startup")
def on_startup():
    init_db()

class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None
    expires_in_hours: Optional[int] = None

# Helper to determine if link is expired
def check_expired(expires_at: Optional[str]) -> bool:
    if not expires_at:
        return False
    expire_dt = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > expire_dt

# --- Web UI Routes ---

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    links = repository.get_recent_links(10)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "base_url": BASE_URL,
        "recent_links": links,
        "created_link": None,
        "error": None
    })

@app.post("/shorten", response_class=HTMLResponse)
def shorten_form(
    request: Request,
    target_url: str = Form(...),
    custom_code: Optional[str] = Form(None),
    expires_in_hours: Optional[str] = Form(None)
):
    target_url = target_url.strip()
    if not validate_url(target_url):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "base_url": BASE_URL,
            "recent_links": repository.get_recent_links(10),
            "error": "Invalid URL format. Please provide a valid http:// or https:// URL."
        }, status_code=status.HTTP_400_BAD_REQUEST)

    code = custom_code.strip() if custom_code and custom_code.strip() else None
    if code:
        if not validate_custom_code(code):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "base_url": BASE_URL,
                "recent_links": repository.get_recent_links(10),
                "error": "Custom slug must be 3-30 alphanumeric characters, dashes, or underscores."
            }, status_code=status.HTTP_400_BAD_REQUEST)
        if repository.is_code_taken(code):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "base_url": BASE_URL,
                "recent_links": repository.get_recent_links(10),
                "error": f"The custom slug '{code}' is already in use. Please pick another."
            }, status_code=status.HTTP_409_CONFLICT)
    else:
        code = generate_code()
        while repository.is_code_taken(code):
            code = generate_code()

    exp_hours = int(expires_in_hours) if expires_in_hours and expires_in_hours.isdigit() else None
    new_link = repository.create_link(target_url, code, exp_hours)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "base_url": BASE_URL,
        "recent_links": repository.get_recent_links(10),
        "created_link": new_link,
        "error": None
    })

@app.get("/stats/{code}", response_class=HTMLResponse)
def view_stats(request: Request, code: str):
    stats = repository.get_link_stats(code)
    if not stats:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=status.HTTP_404_NOT_FOUND)
    
    is_expired = check_expired(stats["link"].get("expires_at"))
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "base_url": BASE_URL,
        "link": stats["link"],
        "recent_clicks": stats["recent_clicks"],
        "top_referrers": stats["top_referrers"],
        "is_expired": is_expired
    })

# --- REST API Endpoints ---

@app.post("/api/shorten", status_code=status.HTTP_201_CREATED)
def api_shorten(payload: ShortenRequest):
    target_url = str(payload.url)
    code = payload.custom_code

    if code:
        if not validate_custom_code(code):
            raise HTTPException(status_code=400, detail="Invalid custom code format")
        if repository.is_code_taken(code):
            raise HTTPException(status_code=409, detail="Custom code already in use")
    else:
        code = generate_code()
        while repository.is_code_taken(code):
            code = generate_code()

    link = repository.create_link(target_url, code, payload.expires_in_hours)
    return {
        "code": link["code"],
        "short_url": f"{BASE_URL}/{link['code']}",
        "target_url": link["target_url"],
        "expires_at": link["expires_at"],
        "created_at": link["created_at"]
    }

@app.get("/api/links/{code}")
def api_get_stats(code: str):
    stats = repository.get_link_stats(code)
    if not stats:
        raise HTTPException(status_code=404, detail="Short link not found")
    stats["is_expired"] = check_expired(stats["link"].get("expires_at"))
    return stats

# --- Redirect Route ---

@app.get("/{code}")
def redirect_to_target(code: str, request: Request):
    link = repository.get_link_by_code(code)
    if not link:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=status.HTTP_404_NOT_FOUND)

    if check_expired(link.get("expires_at")):
        return templates.TemplateResponse("404.html", {"request": request}, status_code=status.HTTP_410_GONE)

    referrer = request.headers.get("referer")
    user_agent = request.headers.get("user-agent")
    repository.record_click(link["id"], referrer, user_agent)

    return RedirectResponse(url=link["target_url"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)
