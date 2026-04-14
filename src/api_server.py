#!/usr/bin/env python3
"""
Mortgage Rate Notifier - REST API Server

Provides REST endpoints for:
- Getting trustworthy refinancing decisions
- Batch processing users
- Health checks
- Metrics tracking

Features:
- FastAPI with automatic OpenAPI/Swagger documentation
- Request/response validation
- Error handling middleware
- CORS support
- Rate limiting ready
- Detailed logging

Usage:
    uvicorn src.api_server:app --host 0.0.0.0 --port 8000
    
    Or with reload:
    uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload

Documentation available at:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
    http://localhost:8000/openapi.json (OpenAPI JSON)
"""

import os
import sys
import logging
import importlib.util
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.exceptions import RequestValidationError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("APIServer")

# Add project root to path for imports from any location
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Check API key
if not os.getenv('OPENAI_API_KEY'):
    logger.warning("OPENAI_API_KEY not set - some features may not work")

# Import rates agent directly (avoid __init__.py dependencies)
RATES_AGENT = None
try:
    spec = importlib.util.spec_from_file_location(
        "rates_agent_module",
        project_root / "agents" / "rates_agent.py"
    )
    rates_agent_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rates_agent_module)
    RATES_AGENT = rates_agent_module.RatesAgent()
    logger.info("RatesAgent loaded successfully")
except Exception as e:
    logger.warning(f"Could not load RatesAgent: {e}")
    RATES_AGENT = None


def load_rag_system():
    """Load RAG modules directly to avoid circular imports."""
    try:
        # Agents are in the agents/ directory at project root
        agents_path = project_root / "agents"
        
        # Load knowledge_base
        spec_kb = importlib.util.spec_from_file_location(
            "knowledge_base",
            agents_path / "knowledge_base.py"
        )
        kb_module = importlib.util.module_from_spec(spec_kb)
        spec_kb.loader.exec_module(kb_module)
        
        # Load rag_agent
        spec_rag = importlib.util.spec_from_file_location(
            "rag_agent",
            agents_path / "rag_agent.py"
        )
        rag_module = importlib.util.module_from_spec(spec_rag)
        rag_module.KnowledgeBase = kb_module.KnowledgeBase
        rag_module.Document = kb_module.Document
        spec_rag.loader.exec_module(rag_module)
        
        # Load trustworthy_decision_agent
        spec_tda = importlib.util.spec_from_file_location(
            "trustworthy_decision_agent",
            agents_path / "trustworthy_decision_agent.py"
        )
        tda_module = importlib.util.module_from_spec(spec_tda)
        tda_module.RAGAgent = rag_module.RAGAgent
        tda_module.ExplanationWithCitations = rag_module.ExplanationWithCitations
        spec_tda.loader.exec_module(tda_module)
        
        return tda_module.TrustworthyDecisionAgent
    except Exception as e:
        logger.error(f"Failed to load RAG system: {e}")
        raise


# ==============================================================================
# Pydantic Models for Request/Response Validation
# ==============================================================================

class UserData(BaseModel):
    """User mortgage and financial information."""
    id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="User name")
    email: Optional[str] = Field(None, description="User email for notifications")
    current_rate: float = Field(..., ge=0.1, le=10.0, description="Current mortgage rate (%)")
    loan_term_years: int = Field(..., ge=5, le=50, description="Original loan term (years)")
    monthly_payment: float = Field(..., gt=0, description="Current monthly payment ($)")
    closing_costs: float = Field(..., ge=0, description="Estimated refinancing closing costs ($)")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    loan_amount: Optional[float] = Field(None, description="Loan amount ($)")
    remaining_term: Optional[int] = Field(None, description="Remaining loan term (months)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "USER-001",
                "name": "John Doe",
                "email": "john@example.com",
                "current_rate": 4.5,
                "loan_term_years": 30,
                "monthly_payment": 1200,
                "closing_costs": 5500,
                "credit_score": 750,
                "loan_amount": 350000,
                "remaining_term": 240
            }
        }


class PredictionData(BaseModel):
    """Market prediction data."""
    predicted_direction: str = Field(..., description="Rate direction: UP, DOWN, or STABLE")
    predicted_average_30d: float = Field(..., description="Predicted average rate in 30 days (%)")
    min_rate: float = Field(..., description="Minimum predicted rate (%)")
    max_rate: float = Field(..., description="Maximum predicted rate (%)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence (0-1)")
    
    @validator('predicted_direction')
    def validate_direction(cls, v):
        if v.upper() not in ['UP', 'DOWN', 'STABLE']:
            raise ValueError('Direction must be UP, DOWN, or STABLE')
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_direction": "DOWN",
                "predicted_average_30d": 4.0,
                "min_rate": 3.9,
                "max_rate": 4.1,
                "confidence": 0.82
            }
        }


class DecisionRequest(BaseModel):
    """Request for trustworthy refinancing decision."""
    user_data: UserData
    prediction: PredictionData
    include_full_report: bool = Field(True, description="Include full decision report")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_data": {
                    "id": "USER-001",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "current_rate": 4.5,
                    "loan_term_years": 30,
                    "monthly_payment": 1200,
                    "closing_costs": 5500,
                    "credit_score": 750,
                    "loan_amount": 350000,
                    "remaining_term": 240
                },
                "prediction": {
                    "predicted_direction": "DOWN",
                    "predicted_average_30d": 4.0,
                    "min_rate": 3.9,
                    "max_rate": 4.1,
                    "confidence": 0.82
                },
                "include_full_report": True
            }
        }


class Citation(BaseModel):
    """Citation for decision support."""
    title: str
    source: str
    relevance_score: float
    quote: str


class DecisionResponse(BaseModel):
    """Response with trustworthy refinancing decision."""
    request_id: str
    status: str
    decision: str
    recommendation: str
    confidence_score: float
    confidence_level: str
    explanation: str
    citations: List[Citation]
    financial_analysis: Dict[str, Any]
    prediction_analysis: Dict[str, Any]
    risk_assessment: str
    full_report: Optional[str] = None
    processing_time_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    """System health status."""
    status: str
    timestamp: str
    rag_system: str
    uptime_seconds: float
    version: str = "1.0.0"
    environment: str


class BatchRequest(BaseModel):
    """Request to process multiple users in batch."""
    users: List[UserData]
    predictions: List[PredictionData]
    parallel: bool = Field(False, description="Process in parallel (experimental)")


class BatchResponse(BaseModel):
    """Response with batch processing results."""
    batch_id: str
    total_users: int
    successful: int
    failed: int
    processing_time_seconds: float
    timestamp: str
    results: List[DecisionResponse]


class RatesResponse(BaseModel):
    """Response with current mortgage rates from free APIs."""
    source: str = Field(..., description="Data source (Freddie Mac, FRED, etc.)")
    timestamp: str = Field(..., description="When rates were fetched")
    rates: Dict[str, float] = Field(..., description="Current rates by loan type")
    week_change: Optional[Dict[str, float]] = Field(None, description="Weekly change in rates")
    confidence: str = Field(..., description="Confidence level (high/medium/low)")
    notice: Optional[str] = Field(None, description="Additional information")


class RatesWithPredictionResponse(BaseModel):
    """Response with current and predicted rates."""
    source: str
    timestamp: str
    current_rates: Dict[str, float] = Field(..., description="Current market rates")
    predicted_rates: Dict[str, float] = Field(..., description="Predicted rates based on direction")
    predicted_direction: str = Field(..., description="Direction of prediction (UP/DOWN/STABLE)")
    prediction_confidence: float = Field(..., description="Confidence in prediction (0-1)")
    confidence_in_rates: str = Field(..., description="Confidence in rate data")


class HistoricalRatesResponse(BaseModel):
    """Response with historical mortgage rates."""
    source: str
    period: str
    start_date: str
    end_date: str
    historical_data: Dict[str, List[Dict[str, Any]]]
    confidence: str


# ==============================================================================
# FastAPI Application
# ==============================================================================

app = FastAPI(
    title="Mortgage Rate Notifier API",
    description="REST API for trustworthy refinancing decisions with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize rate limiter (uses client IP address)
# Default key_func uses remote IP address to identify clients
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={
        "detail": "Rate limit exceeded. Please try again later.",
        "retry_after": "60 seconds"
    }
))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
start_time = datetime.now()
trustworthy_agent = None
request_count = 0


# ==============================================================================
# Startup/Shutdown Events
# ==============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    global trustworthy_agent, start_time
    start_time = datetime.now()
    
    logger.info("="*80)
    logger.info("MORTGAGE RATE NOTIFIER API - STARTING")
    logger.info("="*80)
    
    try:
        logger.info("Loading RAG system...")
        TrustworthyDecisionAgent = load_rag_system()
        trustworthy_agent = TrustworthyDecisionAgent()
        logger.info("RAG system loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load RAG system: {e}")
        trustworthy_agent = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("="*80)
    logger.info("MORTGAGE RATE NOTIFIER API - SHUTTING DOWN")
    logger.info(f"Total requests processed: {request_count}")
    logger.info("="*80)


# ==============================================================================
# Health & Status Endpoints
# ==============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Check API health status."""
    uptime = (datetime.now() - start_time).total_seconds()
    
    return HealthResponse(
        status="healthy" if trustworthy_agent else "degraded",
        timestamp=datetime.now().isoformat(),
        rag_system="ready" if trustworthy_agent else "not-loaded",
        uptime_seconds=uptime,
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development")
    )


@app.get("/", tags=["Root"])
@limiter.limit("60/minute")
async def root(request: Request):
    """API information."""
    return {
        "name": "Mortgage Rate Notifier API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "GET /health",
            "decision": "POST /decision - Generate refinancing decision",
            "batch": "POST /batch - Process multiple users",
            "rates": "GET /rates - Get current mortgage rates",
            "rates_historical": "GET /rates/historical - Get historical rates",
            "rates_predict": "POST /rates/predict - Get predicted rates",
            "metrics": "GET /metrics - System metrics"
        },
        "features": {
            "mortgage_decisions": "AI-powered refinancing recommendations",
            "rate_fetching": "Free rates from Freddie Mac & FRED",
            "batch_processing": "Process 100+ users efficiently",
            "trustworthy_ai": "Decisions backed by citations"
        }
    }



# ==============================================================================
# Decision Endpoints
# ==============================================================================

@app.post("/decision", response_model=DecisionResponse, tags=["Decisions"])
@limiter.limit("30/minute")
async def get_decision(request: Request, req: DecisionRequest) -> DecisionResponse:
    """
    Get a trustworthy refinancing decision with RAG-generated explanations.
    
    This endpoint:
    - Accepts user mortgage data and rate predictions
    - Generates a trustworthy refinancing decision
    - Includes financial analysis and risk assessment
    - Provides citations from authoritative sources
    - Returns confidence scoring (0-100%)
    
    **Response includes:**
    - **decision**: REFINANCE NOW, WAIT 1-2 WEEKS, MONITOR, etc.
    - **confidence_score**: 0-1.0 (0-100%)
    - **citations**: 3+ authoritative sources with quotes
    - **full_report**: Complete analysis with all details
    """
    global request_count
    request_count += 1
    
    if not trustworthy_agent:
        raise HTTPException(
            status_code=503,
            detail="RAG system not initialized. Check logs for startup errors."
        )
    
    try:
        import time
        start = time.time()
        
        # Prepare prediction data
        prediction = {
            'predictions': {
                'predicted_direction': req.prediction.predicted_direction,
                'predicted_average_30d': req.prediction.predicted_average_30d,
                'min_rate': req.prediction.min_rate,
                'max_rate': req.prediction.max_rate
            },
            'reliability': {
                'overall_reliability': req.prediction.confidence
            },
            'financial_analysis': {
                'current_rate': req.user_data.current_rate,
                'potential_monthly_saving': 250,  # Simplified for demo
                'estimated_closing_costs': req.user_data.closing_costs,
                'breakeven_months': 22,  # Simplified for demo
                'remaining_loan_term_months': req.user_data.remaining_term or (req.user_data.loan_term_years * 12),
                'is_financially_safe': True,  # Simplified for demo
                'current_loan_amount': req.user_data.loan_amount or 350000
            }
        }
        
        # Generate decision
        trustworthy_decision = trustworthy_agent.make_trustworthy_decision(
            prediction, 
            req.user_data.dict()
        )
        
        processing_time = (time.time() - start) * 1000  # ms
        
        # Build response
        citations = [
            Citation(
                title=c.title,
                source=c.source,
                relevance_score=c.relevance_score,
                quote=c.quote
            )
            for c in trustworthy_decision.explanation.citations
        ]
        
        full_report = None
        if req.include_full_report:
            full_report = trustworthy_agent.get_full_report(trustworthy_decision)
        
        return DecisionResponse(
            request_id=f"REQ-{request_count:06d}",
            status="success",
            decision=trustworthy_decision.decision,
            recommendation=trustworthy_decision.recommendation,
            confidence_score=trustworthy_decision.confidence_score,
            confidence_level=trustworthy_decision.confidence_level,
            explanation=trustworthy_decision.explanation.explanation,
            citations=citations,
            financial_analysis=trustworthy_decision.financial_analysis,
            prediction_analysis=trustworthy_decision.prediction_analysis,
            risk_assessment=trustworthy_decision.risk_assessment,
            full_report=full_report,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Decision request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Decision generation failed: {str(e)}"
        )


@app.post("/batch", response_model=BatchResponse, tags=["Batch Processing"])
@limiter.limit("10/minute")
async def batch_decisions(request: Request, req: BatchRequest) -> BatchResponse:
    """
    Process multiple users in batch for their refinancing decisions.
    
    Processes up to 100 users efficiently with:
    - Parallel processing support (experimental)
    - Consistent decision logic
    - Aggregated metrics
    
    **Use cases:**
    - Daily processing of 1000+ users
    - Bulk decision generation
    - Performance testing
    """
    global request_count
    
    if not trustworthy_agent:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    if len(req.users) != len(req.predictions):
        raise HTTPException(
            status_code=400,
            detail="Number of users must match number of predictions"
        )
    
    if len(req.users) > 100:
        raise HTTPException(
            status_code=400,
            detail="Batch size limited to 100 users (request has {})".format(len(req.users))
        )
    
    try:
        import time
        start = time.time()
        
        results = []
        successful = 0
        failed = 0
        
        for user, prediction in zip(req.users, req.predictions):
            try:
                request_count += 1
                
                # Prepare prediction
                pred_dict = {
                    'predictions': {
                        'predicted_direction': prediction.predicted_direction,
                        'predicted_average_30d': prediction.predicted_average_30d,
                        'min_rate': prediction.min_rate,
                        'max_rate': prediction.max_rate
                    },
                    'reliability': {'overall_reliability': prediction.confidence},
                    'financial_analysis': {
                        'current_rate': user.current_rate,
                        'potential_monthly_saving': 250,
                        'estimated_closing_costs': user.closing_costs,
                        'breakeven_months': 22,
                        'remaining_loan_term_months': user.remaining_term or (user.loan_term_years * 12),
                        'is_financially_safe': True,
                        'current_loan_amount': user.loan_amount or 350000
                    }
                }
                
                # Generate decision
                decision = trustworthy_agent.make_trustworthy_decision(pred_dict, user.dict())
                
                # Build result
                citations = [
                    Citation(
                        title=c.title,
                        source=c.source,
                        relevance_score=c.relevance_score,
                        quote=c.quote
                    )
                    for c in decision.explanation.citations
                ]
                
                result = DecisionResponse(
                    request_id=f"REQ-{request_count:06d}",
                    status="success",
                    decision=decision.decision,
                    recommendation=decision.recommendation,
                    confidence_score=decision.confidence_score,
                    confidence_level=decision.confidence_level,
                    explanation=decision.explanation.explanation,
                    citations=citations,
                    financial_analysis=decision.financial_analysis,
                    prediction_analysis=decision.prediction_analysis,
                    risk_assessment=decision.risk_assessment,
                    processing_time_ms=0,
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
                successful += 1
                
            except Exception as e:
                logger.error(f"User {user.id} failed: {e}")
                failed += 1
        
        processing_time = time.time() - start
        
        return BatchResponse(
            batch_id=f"BATCH-{request_count:06d}",
            total_users=len(request.users),
            successful=successful,
            failed=failed,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat(),
            results=results
        )
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )


# ==============================================================================
# Metrics Endpoint
# ==============================================================================

@app.get("/metrics", tags=["Metrics"])
@limiter.limit("60/minute")
async def get_metrics(request: Request):
    """Get API metrics and statistics."""
    uptime = (datetime.now() - start_time).total_seconds()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime,
        "total_requests": request_count,
        "status": "healthy" if trustworthy_agent else "degraded",
        "rag_system": "ready" if trustworthy_agent else "not-loaded"
    }


# ==============================================================================
# Mortgage Rates Endpoints
# ==============================================================================

@app.get("/rates", response_model=RatesResponse, tags=["Rates"])
@limiter.limit("100/minute")
async def get_current_rates(request: Request, state: Optional[str] = Query(None, description="US state code (CA, NY, etc.)")):
    """
    Get current mortgage rates from free public sources (Freddie Mac, FRED).
    
    **Features:**
    - 30-year, 15-year, and 5/1 ARM rates
    - Updated weekly
    - Free data from official sources
    - Cached for 1 hour
    
    **Response includes:**
    - Current rates for major loan types
    - Weekly changes
    - Data source and confidence level
    
    **Examples:**
    ```
    GET /rates
    GET /rates?state=CA
    ```
    """
    if not RATES_AGENT:
        raise HTTPException(
            status_code=503,
            detail="Rates service not initialized"
        )
    
    try:
        rates = RATES_AGENT.get_current_rates(state=state)
        
        return RatesResponse(
            source=rates.get('source', 'Unknown'),
            timestamp=rates.get('timestamp', datetime.now().isoformat()),
            rates=rates.get('rates', {}),
            week_change=rates.get('week_change'),
            confidence=rates.get('confidence', 'medium'),
            notice=rates.get('notice')
        )
    except Exception as e:
        logger.error(f"Failed to fetch rates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch rates: {str(e)}"
        )


@app.get("/rates/historical", response_model=HistoricalRatesResponse, tags=["Rates"])
@limiter.limit("50/minute")
async def get_historical_rates(request: Request, days: int = Query(30, ge=1, le=365, description="Number of days of history")):
    """
    Get historical mortgage rates for analysis and trending.
    
    **Features:**
    - Up to 1 year of historical data
    - Daily or weekly data points
    - Useful for trend analysis
    - Requires FRED API setup (free at stlouisfed.org)
    
    **Response includes:**
    - Historical rate data points
    - Date ranges
    - Trend information
    
    **Examples:**
    ```
    GET /rates/historical
    GET /rates/historical?days=90
    ```
    """
    if not RATES_AGENT:
        raise HTTPException(
            status_code=503,
            detail="Rates service not initialized"
        )
    
    try:
        historical = RATES_AGENT.get_historical_rates(days=days)
        
        if 'error' in historical:
            raise HTTPException(
                status_code=500,
                detail=historical['error']
            )
        
        return historical
    except Exception as e:
        logger.error(f"Failed to fetch historical rates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch historical rates: {str(e)}"
        )


@app.post("/rates/predict", response_model=RatesWithPredictionResponse, tags=["Rates"])
@limiter.limit("30/minute")
async def get_rates_with_prediction(
    request: Request,
    prediction_direction: str = Query("DOWN", description="Expected rate direction (UP/DOWN/STABLE)"),
    confidence: float = Query(0.75, ge=0.0, le=1.0, description="Confidence in prediction (0-1)")
):
    """
    Get current rates and estimate predicted rates based on market direction.
    
    **Features:**
    - Combines current real rates with predictions
    - Useful for refinancing decisions
    - Accounts for confidence levels
    
    **Parameters:**
    - `prediction_direction`: UP (rates increase), DOWN (rates decrease), STABLE (no change)
    - `confidence`: How confident in the prediction (0.0 = not sure, 1.0 = very sure)
    
    **Response includes:**
    - Current market rates
    - Predicted rates
    - Direction and confidence metrics
    
    **Examples:**
    ```
    POST /rates/predict?prediction_direction=DOWN&confidence=0.85
    POST /rates/predict?prediction_direction=UP&confidence=0.60
    ```
    """
    if not RATES_AGENT:
        raise HTTPException(
            status_code=503,
            detail="Rates service not initialized"
        )
    
    try:
        predicted = RATES_AGENT.get_rates_for_prediction(
            predicted_direction=prediction_direction.upper(),
            confidence=confidence
        )
        
        return RatesWithPredictionResponse(
            source=predicted.get('source', 'Unknown'),
            timestamp=predicted.get('timestamp', datetime.now().isoformat()),
            current_rates=predicted.get('current_rates', {}),
            predicted_rates=predicted.get('predicted_rates', {}),
            predicted_direction=predicted.get('predicted_direction', 'STABLE'),
            prediction_confidence=predicted.get('prediction_confidence', 0.0),
            confidence_in_rates=predicted.get('confidence_in_rates', 'medium')
        )
    except Exception as e:
        logger.error(f"Failed to calculate predicted rates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate predicted rates: {str(e)}"
        )


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ==============================================================================
# Development Entry Point
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run with: uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    print(f"\n{'='*80}")
    print("MORTGAGE RATE NOTIFIER API SERVER")
    print(f"{'='*80}")
    print(f"Starting server at http://{host}:{port}")
    print(f"Swagger docs: http://{host}:{port}/docs")
    print(f"{'='*80}\n")
    
    uvicorn.run(
        "src.api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
