"""
Lambda Handler for Mortgage Rate Notifier

Adapts the FastAPI application to AWS Lambda + API Gateway format.
Eliminates need for FastAPI/Uvicorn in production.

Key differences from API server:
- AWS Lambda handler format (event, context)
- API Gateway integration
- No FastAPI server overhead
- Cold start optimized
- Parameter Store for secrets

Usage:
    AWS Lambda runtime: python3.11
    Handler: lambda_handler.handler
    
Environment variables:
    FRED_API_KEY - From AWS Parameter Store
    OPENAI_API_KEY - From AWS Parameter Store
    AWS_REGION - Default: us-east-1
"""

import json
import logging
import os
import sys
import base64
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Add layers and project code to path
sys.path.insert(0, '/var/task')
sys.path.insert(0, '/opt/python/lib/python3.11/site-packages')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
ssm_client = boto3.client('ssm', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

def load_api_keys_from_parameter_store():
    """Load API keys from AWS Parameter Store at cold start."""
    try:
        logger.info("Loading API keys from Parameter Store...")
        
        # Fetch FRED API Key
        fred_response = ssm_client.get_parameter(
            Name='/mortgage-rate-notifier/FRED_API_KEY',
            WithDecryption=True
        )
        os.environ['FRED_API_KEY'] = fred_response['Parameter']['Value']
        logger.info("✓ FRED API Key loaded from Parameter Store")
        
        # Fetch OpenAI API Key
        openai_response = ssm_client.get_parameter(
            Name='/mortgage-rate-notifier/OPENAI_API_KEY',
            WithDecryption=True
        )
        os.environ['OPENAI_API_KEY'] = openai_response['Parameter']['Value']
        logger.info("✓ OpenAI API Key loaded from Parameter Store")
        
    except Exception as e:
        logger.error(f"Failed to load API keys from Parameter Store: {e}")
        raise

# Load API keys at cold start
load_api_keys_from_parameter_store()

# Import your orchestration engine
try:
    from src.orchestration_engine import MortgageOrchestrationEngine, NotificationStrategy
    from agents.knowledge_base import KnowledgeBase
    from agents.rag_agent import RAGAgent
    from agents.trustworthy_decision_agent import TrustworthyDecisionAgent
    logger.info("✓ All modules imported successfully")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise

# Global engine instance (reused across invocations to save cold start time)
_orchestration_engine = None
_rag_agent = None
_trustworthy_agent = None

def get_orchestration_engine():
    """Get or create orchestration engine (cached across invocations)."""
    global _orchestration_engine
    if _orchestration_engine is None:
        logger.info("Initializing orchestration engine...")
        _orchestration_engine = MortgageOrchestrationEngine(
            notification_strategy=NotificationStrategy.ALWAYS,
            use_rag=True
        )
    return _orchestration_engine

def get_ragsystem():
    """Get or create RAG system (cached across invocations)."""
    global _rag_agent, _trustworthy_agent
    if _rag_agent is None:
        logger.info("Initializing RAG system...")
        _rag_agent = RAGAgent()
        _trustworthy_agent = TrustworthyDecisionAgent(rag_agent=_rag_agent)
    return _rag_agent, _trustworthy_agent

def format_response(status_code: int, body: Dict[str, Any], is_base64: bool = False) -> Dict[str, Any]:
    """Format response for API Gateway."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps(body) if isinstance(body, dict) else body,
        "isBase64Encoded": is_base64
    }

def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse request body from API Gateway event."""
    body = event.get('body', '{}')
    
    # Handle base64 encoded body
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')
    
    try:
        return json.loads(body) if body else {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {}

def handle_decision(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /decision endpoint
    
    Process a single user's mortgage refinancing decision.
    """
    try:
        body = parse_body(event)
        
        # Validate required fields
        if 'user_data' not in body or 'prediction' not in body:
            return format_response(400, {
                "error": "Missing required fields: user_data, prediction",
                "example": {
                    "user_data": {
                        "id": "USER-001",
                        "name": "John Doe",
                        "current_rate": 4.5,
                        "loan_term_years": 30,
                        "monthly_payment": 1200,
                        "closing_costs": 5500,
                        "credit_score": 750
                    },
                    "prediction": {
                        "predicted_direction": "DOWN",
                        "predicted_average_30d": 4.0,
                        "confidence": 0.82
                    }
                }
            })
        
        # Get orchestration engine
        engine = get_orchestration_engine()
        
        # Process decision
        logger.info(f"Processing decision for user: {body['user_data'].get('id')}")
        result = engine.process_single_decision(
            user_data=body['user_data'],
            prediction=body['prediction'],
            send_email=body.get('send_email', False)
        )
        
        return format_response(200, {
            "success": True,
            "request_id": result.get('request_id'),
            "user_id": result.get('user_id'),
            "decision": result.get('decision'),
            "reasoning": result.get('reasoning'),
            "confidence": result.get('confidence'),
            "citations": result.get('citations', []),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in handle_decision: {e}", exc_info=True)
        return format_response(500, {
            "error": "Internal server error",
            "message": str(e)
        })

def handle_batch(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /batch endpoint
    
    Process multiple users' mortgage refinancing decisions.
    Supports up to 100 users per request.
    """
    try:
        body = parse_body(event)
        
        if 'users' not in body:
            return format_response(400, {
                "error": "Missing required field: users",
                "note": "Expected array of {user_data, prediction} objects"
            })
        
        users = body['users']
        if not isinstance(users, list):
            return format_response(400, {
                "error": "users must be an array"
            })
        
        if len(users) > 100:
            return format_response(400, {
                "error": "Maximum 100 users per batch",
                "received": len(users)
            })
        
        # Get orchestration engine
        engine = get_orchestration_engine()
        
        # Process batch
        logger.info(f"Processing batch of {len(users)} users")
        results = engine.process_batch(
            users=users,
            send_emails=body.get('send_emails', False)
        )
        
        return format_response(200, {
            "success": True,
            "batch_id": results.get('batch_id'),
            "total": len(users),
            "processed": results.get('processed_count', 0),
            "failed": results.get('failed_count', 0),
            "results": results.get('decisions', []),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error in handle_batch: {e}", exc_info=True)
        return format_response(500, {
            "error": "Internal server error",
            "message": str(e)
        })

def handle_health(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /health endpoint - simple health check."""
    try:
        # Try to import and verify key components
        engine = get_orchestration_engine()
        
        return format_response(200, {
            "status": "healthy",
            "service": "MortgageRateNotifier",
            "version": "2.0.0-lambda",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "orchestration": "ok",
                "rag_system": "ok" if engine.use_rag else "disabled",
                "aws_region": os.getenv('AWS_REGION', 'us-east-1')
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return format_response(503, {
            "status": "unhealthy",
            "error": str(e)
        })

def handle_metrics(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /metrics endpoint - performance metrics."""
    try:
        engine = get_orchestration_engine()
        
        return format_response(200, {
            "metrics": {
                "cache_hits": engine.orchestrator.decision_cache_hits if hasattr(engine.orchestrator, 'decision_cache_hits') else 0,
                "cache_misses": engine.orchestrator.decision_cache_misses if hasattr(engine.orchestrator, 'decision_cache_misses') else 0,
                "average_decision_time_ms": int(engine.orchestrator.avg_decision_time * 1000) if hasattr(engine.orchestrator, 'avg_decision_time') else 0,
                "total_decisions": engine.orchestrator.total_decisions if hasattr(engine.orchestrator, 'total_decisions') else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return format_response(500, {
            "error": "Could not retrieve metrics",
            "message": str(e)
        })

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function.
    
    Routes requests to appropriate handler based on path and method.
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
    
    Returns:
        API Gateway formatted response
    """
    logger.info(f"Received request: {event.get('httpMethod')} {event.get('path')}")
    
    # Extract request details
    http_method = event.get('httpMethod', 'GET').upper()
    path = event.get('path', '/').strip('/')
    
    # Route to appropriate handler
    try:
        if path == 'decision' and http_method == 'POST':
            return handle_decision(event)
        
        elif path == 'batch' and http_method == 'POST':
            return handle_batch(event)
        
        elif path == 'health' and http_method == 'GET':
            return handle_health(event)
        
        elif path == 'metrics' and http_method == 'GET':
            return handle_metrics(event)
        
        elif http_method == 'OPTIONS':
            # Handle CORS preflight
            return format_response(200, {})
        
        else:
            return format_response(404, {
                "error": "Not found",
                "available_endpoints": [
                    "POST /decision - Single decision",
                    "POST /batch - Batch decisions",
                    "GET /health - Health check",
                    "GET /metrics - Performance metrics"
                ]
            })
    
    except Exception as e:
        logger.error(f"Unexpected error in handler: {e}", exc_info=True)
        return format_response(500, {
            "error": "Internal server error",
            "message": str(e),
            "request_id": context.request_id if context else None
        })

# Warm-up handler for kept-alive Lambda
def warmup(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Warm-up handler to keep Lambda warm and reduce cold starts.
    
    Called by CloudWatch Events every 5 minutes.
    """
    logger.info("Lambda warmup triggered")
    try:
        # Initialize engines to pre-load code
        engine = get_orchestration_engine()
        logger.info("✓ Warmup completed")
        return {"statusCode": 200, "body": "warmed"}
    except Exception as e:
        logger.error(f"Warmup failed: {e}")
        return {"statusCode": 500, "body": str(e)}
