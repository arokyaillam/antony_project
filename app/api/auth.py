from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from app.services.upstox_auth import UpstoxAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

class AuthConfig(BaseModel):
    api_key: str
    api_secret: str
    redirect_uri: str

@router.post("/configure")
async def configure_auth(config: AuthConfig):
    try:
        await UpstoxAuthService.save_credentials(
            config.api_key, 
            config.api_secret, 
            config.redirect_uri
        )
        return {"message": "Credentials saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/login")
async def login():
    try:
        login_url = await UpstoxAuthService.get_login_url()
        return RedirectResponse(url=login_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def callback(code: str):
    """
    OAuth callback - Token save பண்ணி frontend dashboard-க்கு redirect
    """
    try:
        access_token = await UpstoxAuthService.generate_access_token(code)
        # Token save ஆச்சு, frontend dashboard-க்கு redirect பண்ணு
        return RedirectResponse(url="http://localhost:5173/dashboard")
    except Exception as e:
        # Error ஆனா frontend-ல error page-க்கு redirect பண்ணு
        return RedirectResponse(url=f"http://localhost:5173/auth/error?message={str(e)}")

