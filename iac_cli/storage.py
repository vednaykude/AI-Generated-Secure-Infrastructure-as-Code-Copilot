import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import time
from rich.console import Console
from dataclasses import dataclass, asdict
import hashlib
import backoff
from datetime import datetime, timedelta
import uuid

console = Console()

@dataclass
class PricingCacheConfig:
    """Configuration for different types of pricing data."""
    ON_DEMAND = {
        'ttl_days': 7,  # On-demand prices change less frequently
        'description': 'On-demand instance pricing'
    }
    SPOT = {
        'ttl_minutes': 10,  # Spot prices can change every 5 minutes
        'description': 'Spot instance pricing'
    }
    RESERVED = {
        'ttl_days': 30,  # Reserved instance pricing is very stable
        'description': 'Reserved instance pricing'
    }
    STORAGE = {
        'ttl_days': 30,  # Storage pricing is very stable
        'description': 'Storage pricing'
    }

@dataclass
class CostHistoryConfig:
    """Configuration for cost history retention periods."""
    # Cost history is used for:
    # 1. Short-term analysis (last 30 days) - For immediate cost optimization
    # 2. Medium-term analysis (last 90 days) - For trend analysis
    # 3. Long-term analysis (last 365 days) - For annual planning
    SHORT_TERM = {
        'ttl_days': 30,
        'description': 'Short-term cost history for immediate optimization'
    }
    MEDIUM_TERM = {
        'ttl_days': 90,
        'description': 'Medium-term cost history for trend analysis'
    }
    LONG_TERM = {
        'ttl_days': 365,
        'description': 'Long-term cost history for annual planning'
    }

@dataclass
class UserPreferences:
    default_region: str = "us-east-1"
    cost_threshold: float = 1000.0
    notification_email: Optional[str] = None
    preferred_instance_types: List[str] = None
    optimization_preferences: Dict[str, bool] = None
    cost_history_retention: str = 'MEDIUM_TERM'  # Default to 90 days retention

    def validate(self) -> bool:
        """Validate user preferences data."""
        if not isinstance(self.default_region, str):
            return False
        if not isinstance(self.cost_threshold, (int, float)) or self.cost_threshold < 0:
            return False
        if self.notification_email and not '@' in self.notification_email:
            return False
        if self.preferred_instance_types and not all(isinstance(x, str) for x in self.preferred_instance_types):
            return False
        if self.optimization_preferences and not all(isinstance(v, bool) for v in self.optimization_preferences.values()):
            return False
        if self.cost_history_retention not in ['SHORT_TERM', 'MEDIUM_TERM', 'LONG_TERM']:
            return False
        return True

@dataclass
class CostHistory:
    """
    Represents a cost history record for a resource.
    
    This is used to track estimated costs over time for:
    1. Cost trend analysis
    2. Identifying cost spikes
    3. Validating cost optimization recommendations
    4. Historical cost analysis
    
    Attributes:
        timestamp: When the cost was recorded
        resource_type: Type of AWS resource (e.g., 'aws_instance', 'aws_db_instance')
        resource_id: Unique identifier for the resource
        cost: Estimated cost in USD
        region: AWS region where the resource is deployed
        tags: Resource tags for better organization and tracking
    """
    timestamp: float
    resource_type: str
    resource_id: str
    cost: float
    region: str
    tags: Dict[str, str]

    def validate(self) -> bool:
        """Validate cost history data."""
        if not isinstance(self.timestamp, (int, float)) or self.timestamp < 0:
            return False
        if not isinstance(self.resource_type, str):
            return False
        if not isinstance(self.resource_id, str):
            return False
        if not isinstance(self.cost, (int, float)) or self.cost < 0:
            return False
        if not isinstance(self.region, str):
            return False
        if not isinstance(self.tags, dict):
            return False
        return True

class StorageManager:
    def __init__(self, region_name: str = "us-east-1"):
        self.region = region_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        self.ssm = boto3.client('ssm', region_name=region_name)
        
        # Initialize tables
        self._init_tables()
        
        # Cache configuration
        self.cache_bucket = f"iac-cli-cache-{uuid.uuid4().hex[:8]}"
        self._init_s3_bucket()

    def _init_tables(self):
        """Initialize DynamoDB tables if they don't exist."""
        try:
            # Pricing Cache Table
            self.pricing_table = self.dynamodb.create_table(
                TableName='IacCliPricingCache',
                KeySchema=[
                    {'AttributeName': 'service', 'KeyType': 'HASH'},
                    {'AttributeName': 'cache_key', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'service', 'AttributeType': 'S'},
                    {'AttributeName': 'cache_key', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                SSESpecification={
                    'Enabled': True,
                    'SSEType': 'KMS'
                },
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
            
            # User Preferences Table
            self.preferences_table = self.dynamodb.create_table(
                TableName='IacCliUserPreferences',
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                SSESpecification={
                    'Enabled': True,
                    'SSEType': 'KMS'
                }
            )
            
            # Cost History Table
            self.cost_history_table = self.dynamodb.create_table(
                TableName='IacCliCostHistory',
                KeySchema=[
                    {'AttributeName': 'resource_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'resource_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'},
                    {'AttributeName': 'region', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'RegionTimestampIndex',
                        'KeySchema': [
                            {'AttributeName': 'region', 'KeyType': 'HASH'},
                            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                SSESpecification={
                    'Enabled': True,
                    'SSEType': 'KMS'
                },
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                # Tables already exist
                self.pricing_table = self.dynamodb.Table('IacCliPricingCache')
                self.preferences_table = self.dynamodb.Table('IacCliUserPreferences')
                self.cost_history_table = self.dynamodb.Table('IacCliCostHistory')
            else:
                raise

    def _init_s3_bucket(self):
        """Initialize S3 bucket for larger data storage."""
        try:
            self.s3.create_bucket(
                Bucket=self.cache_bucket,
                CreateBucketConfiguration={'LocationConstraint': self.region}
            )
            
            # Enable server-side encryption
            self.s3.put_bucket_encryption(
                Bucket=self.cache_bucket,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            
            # Set bucket policy
            bucket_policy = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Sid': 'EnforceEncryption',
                        'Effect': 'Deny',
                        'Principal': '*',
                        'Action': 's3:PutObject',
                        'Resource': f'arn:aws:s3:::{self.cache_bucket}/*',
                        'Condition': {
                            'StringNotEquals': {
                                's3:x-amz-server-side-encryption': 'AES256'
                            }
                        }
                    }
                ]
            }
            self.s3.put_bucket_policy(
                Bucket=self.cache_bucket,
                Policy=json.dumps(bucket_policy)
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'BucketAlreadyOwnedByYou':
                raise

    def _get_ttl_timestamp(self, pricing_type: str) -> int:
        """Get TTL timestamp based on pricing type."""
        config = getattr(PricingCacheConfig, pricing_type.upper(), PricingCacheConfig.ON_DEMAND)
        
        if 'ttl_minutes' in config:
            return int((datetime.now() + timedelta(minutes=config['ttl_minutes'])).timestamp())
        else:
            return int((datetime.now() + timedelta(days=config['ttl_days'])).timestamp())

    def _get_cost_history_ttl(self, retention_type: str = 'MEDIUM_TERM') -> int:
        """Get TTL timestamp for cost history based on retention type."""
        config = getattr(CostHistoryConfig, retention_type.upper(), CostHistoryConfig.MEDIUM_TERM)
        return int((datetime.now() + timedelta(days=config['ttl_days'])).timestamp())

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def store_pricing_data(self, service: str, data: Dict[str, Any], pricing_type: str = 'ON_DEMAND'):
        """Store pricing data in DynamoDB with retry logic."""
        try:
            timestamp = int(time.time())
            cache_key = f"{service}_{hashlib.sha256(json.dumps(data).encode()).hexdigest()}"
            
            # Get TTL based on pricing type
            ttl = self._get_ttl_timestamp(pricing_type)
            
            self.pricing_table.put_item(
                Item={
                    'service': service,
                    'cache_key': cache_key,
                    'timestamp': timestamp,
                    'data': data,
                    'ttl': ttl,
                    'pricing_type': pricing_type
                }
            )
        except Exception as e:
            console.print(f"[red]Error storing pricing data: {e}[/red]")
            raise

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def get_pricing_data(self, service: str, pricing_type: str = 'ON_DEMAND') -> Optional[Dict[str, Any]]:
        """Retrieve pricing data from DynamoDB with retry logic."""
        try:
            current_time = int(time.time())
            response = self.pricing_table.query(
                KeyConditionExpression='service = :s AND cache_key BEGINS_WITH :p',
                FilterExpression='pricing_type = :t',
                ExpressionAttributeValues={
                    ':s': service,
                    ':p': f"{service}_",
                    ':t': pricing_type
                },
                ScanIndexForward=False,
                Limit=1
            )
            
            if response['Items']:
                item = response['Items'][0]
                # Check if the data is still valid based on pricing type
                config = getattr(PricingCacheConfig, pricing_type.upper(), PricingCacheConfig.ON_DEMAND)
                max_age = config.get('ttl_minutes', config.get('ttl_days', 7) * 24 * 60) * 60
                
                if current_time - item['timestamp'] < max_age:
                    return item['data']
        except Exception as e:
            console.print(f"[red]Error retrieving pricing data: {e}[/red]")
            raise
        return None

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def store_user_preferences(self, user_id: str, preferences: UserPreferences):
        """Store user preferences in DynamoDB with validation and retry logic."""
        try:
            if not preferences.validate():
                raise ValueError("Invalid user preferences data")
                
            self.preferences_table.put_item(
                Item={
                    'user_id': user_id,
                    'preferences': asdict(preferences)
                }
            )
        except Exception as e:
            console.print(f"[red]Error storing user preferences: {e}[/red]")
            raise

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Retrieve user preferences from DynamoDB with retry logic."""
        try:
            response = self.preferences_table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' in response:
                return UserPreferences(**response['Item']['preferences'])
        except Exception as e:
            console.print(f"[red]Error retrieving user preferences: {e}[/red]")
            raise
        return None

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def store_cost_history(self, cost_history: CostHistory, retention_type: str = 'MEDIUM_TERM'):
        """Store cost history in DynamoDB with validation and retry logic."""
        try:
            if not cost_history.validate():
                raise ValueError("Invalid cost history data")
                
            # Get TTL based on retention type
            ttl = self._get_cost_history_ttl(retention_type)
            
            self.cost_history_table.put_item(
                Item={
                    **asdict(cost_history),
                    'ttl': ttl,
                    'retention_type': retention_type
                }
            )
        except Exception as e:
            console.print(f"[red]Error storing cost history: {e}[/red]")
            raise

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def get_cost_history(self, resource_id: str, start_time: float, end_time: float) -> List[CostHistory]:
        """Retrieve cost history from DynamoDB with retry logic."""
        try:
            response = self.cost_history_table.query(
                KeyConditionExpression='resource_id = :r AND timestamp BETWEEN :s AND :e',
                ExpressionAttributeValues={
                    ':r': resource_id,
                    ':s': start_time,
                    ':e': end_time
                }
            )
            
            return [CostHistory(**item) for item in response['Items']]
        except Exception as e:
            console.print(f"[red]Error retrieving cost history: {e}[/red]")
            raise
        return []

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def store_large_data(self, key: str, data: Any):
        """Store larger datasets in S3 with retry logic."""
        try:
            self.s3.put_object(
                Bucket=self.cache_bucket,
                Key=key,
                Body=json.dumps(data),
                ServerSideEncryption='AES256'
            )
        except Exception as e:
            console.print(f"[red]Error storing data in S3: {e}[/red]")
            raise

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def get_large_data(self, key: str) -> Optional[Any]:
        """Retrieve larger datasets from S3 with retry logic."""
        try:
            response = self.s3.get_object(
                Bucket=self.cache_bucket,
                Key=key
            )
            return json.loads(response['Body'].read())
        except Exception as e:
            console.print(f"[red]Error retrieving data from S3: {e}[/red]")
            raise
        return None

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def store_secure_data(self, key: str, value: str):
        """Store sensitive data in Parameter Store with retry logic."""
        try:
            self.ssm.put_parameter(
                Name=f"/iac-cli/{key}",
                Value=value,
                Type='SecureString',
                Overwrite=True
            )
        except Exception as e:
            console.print(f"[red]Error storing secure data: {e}[/red]")
            raise

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    def get_secure_data(self, key: str) -> Optional[str]:
        """Retrieve sensitive data from Parameter Store with retry logic."""
        try:
            response = self.ssm.get_parameter(
                Name=f"/iac-cli/{key}",
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except Exception as e:
            console.print(f"[red]Error retrieving secure data: {e}[/red]")
            raise
        return None 