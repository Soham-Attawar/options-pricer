# ============================================================
# NIFTY OPTIONS PRICER - FastAPI Backend
# ============================================================

# --- IMPORTS ---
from fastapi import FastAPI, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from market_data import get_nifty_price, get_nifty_volatility, get_next_expiry, get_monthly_expiry, get_banknifty_price, get_banknifty_volatility, get_banknifty_expiry
from core import price_option
from database import SessionLocal, APIKey, APIUsage

# --- CREATE APP ---
app = FastAPI(title="Nifty Options Pricer API", version="1.0")

# --- DATABASE SESSION ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- REQUEST MODEL ---
class OptionRequest(BaseModel):
    index: str
    strike: float
    expiry_type: str

# --- AUTHENTICATION FUNCTION ---
def verify_api_key(x_api_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API key missing. Include X-API-Key in headers."
        )

    # Look up key in database
    key_record = db.query(APIKey).filter(APIKey.api_key == x_api_key).first()

    if key_record is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key."
        )

    if key_record.calls_remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="API call limit reached. Upgrade your plan."
        )

    # Deduct one call and save to database
    key_record.calls_remaining -= 1
    db.commit()

    return key_record

# --- ROOT ENDPOINT ---
@app.get("/")
def read_root():
    return {"message": "Welcome to Nifty Options Pricer API"}

# --- PRICE OPTION ENDPOINT ---
@app.post("/price-option")
def price_option_endpoint(request: OptionRequest, key_record = Depends(verify_api_key), db: Session = Depends(get_db)):

    # Fetch market data
    if request.index.lower() == "nifty":
        S0 = get_nifty_price()
        sigma = get_nifty_volatility()
        weekly_date, weekly_T, weekly_days = get_next_expiry()
        monthly_date, monthly_T, monthly_days = get_monthly_expiry()
    else:
        S0 = get_banknifty_price()
        sigma = get_banknifty_volatility()
        weekly_date, weekly_T, weekly_days = get_banknifty_expiry()
        monthly_date, monthly_T, monthly_days = get_monthly_expiry()

    # Select expiry
    if request.expiry_type.lower() == "weekly":
        T = weekly_T
        expiry_date = weekly_date
        days_remaining = weekly_days
        paths = 100000
    else:
        T = monthly_T
        expiry_date = monthly_date
        days_remaining = monthly_days
        paths = 50000

    # Price the option
    results = price_option(S0, request.strike, T, r=0.065, sigma=sigma, paths=paths)

    # Log usage to database
    usage = APIUsage(
        api_key=key_record.api_key,
        index=request.index,
        strike=float(request.strike),
        expiry_type=request.expiry_type,
        call_price=float(results['call_price']),
        put_price=float(results['put_price'])
    )
    db.add(usage)
    db.commit()

    # Return response
    return {
        "user_id": key_record.user_id,
        "calls_remaining": key_record.calls_remaining,
        "index": request.index,
        "current_price": S0,
        "strike": request.strike,
        "expiry_date": expiry_date,
        "days_to_expiry": days_remaining,
        "volatility": round(sigma * 100, 2),
        "call_price_mc": round(results['call_price'], 2),
        "call_price_bs": round(results['BS_call'], 2),
        "put_price_mc": round(results['put_price'], 2),
        "put_price_bs": round(results['BS_put'], 2),
        "greeks": {
            "delta_call": round(results['delta_call'], 4),
            "delta_put": round(results['delta_put'], 4),
            "gamma": round(results['gamma'], 6),
            "theta_call": round(results['theta_call'], 2),
            "theta_put": round(results['theta_put'], 2),
            "vega": round(results['vega'], 2)
        }
    }