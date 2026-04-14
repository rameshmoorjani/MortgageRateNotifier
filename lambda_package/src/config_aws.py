"""
AWS Systems Manager Parameter Store Configuration

Fetches sensitive configuration from AWS Parameter Store for secure deployments.
Falls back to environment variables for local development.

Usage:
    from src.config_aws import get_fred_api_key, get_openai_api_key
    
    fred_key = get_fred_api_key()  # Tries env var first, then Parameter Store
    openai_key = get_openai_api_key()
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import boto3, but don't fail if it's not installed (for local dev)
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.debug("boto3 not installed - will use environment variables only")


class AWSParameterStore:
    """Fetch secrets from AWS Systems Manager Parameter Store"""
    
    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize Parameter Store client
        
        Args:
            region: AWS region (default: us-east-1)
        """
        self.region = region
        self.cache = {}
        self.ssm = None
        
        if BOTO3_AVAILABLE:
            try:
                self.ssm = boto3.client('ssm', region_name=region)
                logger.info(f"✓ AWS Systems Manager Parameter Store initialized (region: {region})")
            except Exception as e:
                logger.warning(f"Failed to initialize boto3 client: {e}")
    
    def get_parameter(self, parameter_name: str, decrypt: bool = True) -> Optional[str]:
        """
        Get parameter from Parameter Store
        
        Args:
            parameter_name: Full parameter name (e.g., /mortgage-rate-notifier/FRED_API_KEY)
            decrypt: If True, decrypt SecureString parameters
        
        Returns:
            Parameter value or None if not found
        """
        # Check cache first
        if parameter_name in self.cache:
            return self.cache[parameter_name]
        
        # Return None if boto3 not available
        if not self.ssm:
            logger.debug(f"Parameter Store client not available for: {parameter_name}")
            return None
        
        try:
            response = self.ssm.get_parameter(
                Name=parameter_name,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            self.cache[parameter_name] = value
            logger.info(f"✓ Retrieved parameter from Parameter Store: {parameter_name}")
            return value
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.debug(f"Parameter not found in Parameter Store: {parameter_name}")
            else:
                logger.error(f"Error retrieving parameter {parameter_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving parameter {parameter_name}: {e}")
            return None
    
    def clear_cache(self):
        """Clear cached values"""
        self.cache.clear()
        logger.debug("Parameter Store cache cleared")


# Initialize Parameter Store client
_parameter_store = AWSParameterStore(region=os.getenv('AWS_REGION', 'us-east-1'))


def get_fred_api_key() -> Optional[str]:
    """
    Get FRED API key from environment or Parameter Store
    
    Priority:
    1. FRED_API_KEY environment variable (local development)
    2. /mortgage-rate-notifier/FRED_API_KEY from Parameter Store (production)
    
    Returns:
        API key or None if not found
    """
    # First check environment variable (for local dev)
    env_key = os.getenv('FRED_API_KEY')
    if env_key:
        logger.debug("✓ Using FRED API key from environment variable (local dev)")
        return env_key
    
    # For production, use Parameter Store
    try:
        key = _parameter_store.get_parameter('/mortgage-rate-notifier/FRED_API_KEY')
        if key:
            logger.debug("✓ Using FRED API key from AWS Parameter Store")
            return key
    except Exception as e:
        logger.error(f"Failed to get FRED API key from Parameter Store: {e}")
    
    logger.warning("⚠ FRED API key not found in environment or Parameter Store")
    return None


def get_openai_api_key() -> Optional[str]:
    """
    Get OpenAI API key from environment or Parameter Store
    
    Priority:
    1. OPENAI_API_KEY environment variable (local development)
    2. /mortgage-rate-notifier/OPENAI_API_KEY from Parameter Store (production)
    
    Returns:
        API key or None if not found
    """
    # First check environment variable (for local dev)
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        logger.debug("✓ Using OpenAI API key from environment variable (local dev)")
        return env_key
    
    # For production, use Parameter Store
    try:
        key = _parameter_store.get_parameter('/mortgage-rate-notifier/OPENAI_API_KEY')
        if key:
            logger.debug("✓ Using OpenAI API key from AWS Parameter Store")
            return key
    except Exception as e:
        logger.error(f"Failed to get OpenAI API key from Parameter Store: {e}")
    
    logger.warning("⚠ OpenAI API key not found in environment or Parameter Store")
    return None


def get_api_parameter(parameter_name: str) -> Optional[str]:
    """
    Get any custom parameter from Parameter Store
    
    Args:
        parameter_name: Full parameter name
    
    Returns:
        Parameter value or None
    """
    return _parameter_store.get_parameter(parameter_name)


if __name__ == '__main__':
    # Test script
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing AWS Parameter Store Configuration:")
    print("-" * 50)
    
    fred_key = get_fred_api_key()
    if fred_key:
        print(f"✓ FRED API Key: {fred_key[:10]}...")
    else:
        print("✗ FRED API Key: Not found")
    
    openai_key = get_openai_api_key()
    if openai_key:
        print(f"✓ OpenAI API Key: {openai_key[:10]}...")
    else:
        print("✗ OpenAI API Key: Not found")
    
    print("-" * 50)
