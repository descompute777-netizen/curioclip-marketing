"""Pydantic models for API request/response."""
from pydantic import BaseModel, Field
from typing import Optional


class AccountIn(BaseModel):
    name: str
    handle: str
    platform: str = "tiktok"
    niche: Optional[str] = None
    followers_current: int = 0
    followers_goal: int = 10000
    color: str = "#fbbf24"
    notes: Optional[str] = None


class VideoIn(BaseModel):
    account_id: int
    video_code: Optional[str] = None
    guion_id: Optional[str] = None
    title: str
    hook: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    niche: Optional[str] = None
    duration_s: Optional[float] = None
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    status: str = "draft"
    vscore_predicted: Optional[float] = None
    scheduled_at: Optional[str] = None
    hypothesis: Optional[str] = None


class SuggestionIn(BaseModel):
    source_url: str
    source_platform: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    view_count: Optional[int] = None
    duration_s: Optional[float] = None
    notes: Optional[str] = None
    added_by: str = "user"


class MetricsIn(BaseModel):
    video_id: int
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    retention_avg: Optional[float] = None
    hook_rate: Optional[float] = None


class AutomationIn(BaseModel):
    agent: str
    action: str
    account_id: Optional[int] = None
    payload: Optional[dict] = None
    scheduled_for: Optional[str] = None


class VideoStatusUpdate(BaseModel):
    status: str
    vscore_actual: Optional[float] = None
    published_at: Optional[str] = None
    external_url: Optional[str] = None
    outcome: Optional[str] = None


class FeedbackIn(BaseModel):
    type: str = "sugerencia"
    priority: str = "normal"
    message: str
    context: Optional[str] = None
