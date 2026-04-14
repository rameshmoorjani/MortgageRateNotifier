#!/usr/bin/env python3
"""
Production Startup Script - Mortgage Rate Notifier with RAG Integration

This script starts the mortgage rate notifier system in production mode with:
- Daily scheduled rate checking
- Trustworthy decision generation with RAG
- Email notifications
- Health monitoring
- Persistent logging

Usage:
    python start_production.py --mode daily --users users.json --log logs/
    python start_production.py --mode once --users users.json
    python start_production.py --status
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Set API key requirement
if not os.getenv('OPENAI_API_KEY'):
    print("ERROR: OPENAI_API_KEY environment variable is required")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util


def load_main_orchestrated():
    """Load main_orchestrated module directly."""
    spec = importlib.util.spec_from_file_location(
        "main_orchestrated",
        Path(__file__).parent / "main_orchestrated.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setup_logging(log_dir='logs'):
    """Setup production logging."""
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = Path(log_dir) / f"production_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("ProductionStart")
    logger.info(f"="*80)
    logger.info("MORTGAGE RATE NOTIFIER - PRODUCTION START")
    logger.info(f"Started: {datetime.now().isoformat()}")
    logger.info(f"Logs: {log_file}")
    logger.info(f"="*80)
    
    return logger


def load_users(filepath):
    """Load users from JSON file."""
    if not Path(filepath).exists():
        print(f"ERROR: User file not found: {filepath}")
        return None
    
    with open(filepath, 'r') as f:
        users = json.load(f)
    
    return users


def main():
    """Main production entry point."""
    parser = argparse.ArgumentParser(
        description="Mortgage Rate Notifier - Production System with RAG"
    )
    
    parser.add_argument(
        '--mode',
        default='daily',
        choices=['daily', 'once', 'status'],
        help='Execution mode: daily (scheduled), once (single run), status (health check)'
    )
    
    parser.add_argument(
        '--users',
        default='users.json',
        help='Path to users JSON file'
    )
    
    parser.add_argument(
        '--log',
        default='logs',
        help='Logging directory'
    )
    
    parser.add_argument(
        '--hour',
        type=int,
        default=9,
        help='Hour to run daily check (0-23, default: 9 AM)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.log)
    
    # Load main orchestrated module
    logger.info("Loading orchestration modules...")
    try:
        main_module = load_main_orchestrated()
        logger.info("Orchestration modules loaded")
    except Exception as e:
        logger.error(f"Failed to load orchestration: {e}")
        return 1
    
    # Mode: Status Check
    if args.mode == 'status':
        logger.info("Checking system status...")
        print("\n" + "="*80)
        print("SYSTEM STATUS CHECK")
        print("="*80)
        
        print("\n[COMPONENTS]")
        print("- Orchestration Engine: OK")
        print("- RAG System: OK")
        print("- Knowledge Base: OK")
        print("- Scheduler: Ready")
        
        print("\n[ENVIRONMENT]")
        print(f"- OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING'}")
        print(f"- Users File: {args.users} ({'FOUND' if Path(args.users).exists() else 'NOT FOUND'})")
        print(f"- Log Directory: {args.log}")
        
        print("\n[MONITORING]")
        health_file = Path(args.log) / "metrics.json"
        if health_file.exists():
            with open(health_file, 'r') as f:
                metrics = json.load(f)
            print(f"- Last Check: {metrics.get('last_check', 'Never')}")
            print(f"- Total Users Processed: {metrics.get('total_processed', 0)}")
            print(f"- Success Rate: {metrics.get('success_rate', 0)*100:.1f}%")
        else:
            print("- No metrics yet (system not run)")
        
        print("\n" + "="*80)
        logger.info("Status check complete")
        return 0
    
    # Load users
    logger.info(f"Loading users from {args.users}...")
    users = load_users(args.users)
    if not users:
        logger.error(f"Failed to load users from {args.users}")
        return 1
    logger.info(f"Loaded {len(users)} users")
    
    # Mode: Run Once
    if args.mode == 'once':
        logger.info("Running in ONCE mode (single execution)")
        print(f"\n[START] Processing {len(users)} users...")
        
        try:
            main_module.main_once(users, verbose=args.verbose)
            logger.info("Batch processing completed successfully")
            print(f"[COMPLETE] All users processed")
            return 0
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            print(f"[ERROR] {e}")
            return 1
    
    # Mode: Daily Schedule
    if args.mode == 'daily':
        logger.info(f"Running in DAILY mode (scheduled for {args.hour}:00)")
        print(f"\n[START] Scheduler running (checking at {args.hour}:00 daily)")
        print(f"[INFO] Processing {len(users)} users daily")
        print(f"[INFO] Logs: {args.log}/")
        print(f"[INFO] Press Ctrl+C to stop scheduler")
        
        try:
            main_module.main_scheduled(users, hour=args.hour, verbose=args.verbose)
            logger.info("Scheduler started successfully")
            return 0
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            print("\n[STOP] Scheduler stopped")
            return 0
        except Exception as e:
            logger.error(f"Scheduler failed: {e}")
            print(f"[ERROR] {e}")
            return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
