import boto3
from typing import Dict, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
import json
from functools import lru_cache
from botocore.exceptions import ClientError
import time
from pathlib import Path
import os

console = Console()

@dataclass
class ResourceCost:
    resource_type: str
    resource_name: str
    estimated_cost: float
    currency: str = "USD"
    period: str = "monthly"

@dataclass
class CostOptimization:
    resource_type: str
    resource_id: str
    current_cost: float
    suggested_cost: float
    recommendation: str

class CostEstimator:
    def __init__(self, region_name: str = "us-east-1"):
        self.pricing_client = boto3.client('pricing', region_name=region_name)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region_name)
        self.region = region_name

    @lru_cache(maxsize=1000)
    def _get_ec2_pricing(self, instance_type: str, os: str = 'Linux', tenancy: str = 'Shared') -> float:
        """Get EC2 instance pricing directly from AWS Pricing API."""
        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': tenancy},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                ]
            )
            
            if response['PriceList']:
                price_data = json.loads(response['PriceList'][0])
                price = float(price_data['terms']['OnDemand'][list(price_data['terms']['OnDemand'].keys())[0]]['priceDimensions'][list(price_data['terms']['OnDemand'][list(price_data['terms']['OnDemand'].keys())[0]]['priceDimensions'].keys())[0]]['pricePerUnit']['USD'])
                return price
        except ClientError as e:
            console.print(f"[red]Error getting EC2 pricing: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error getting EC2 pricing: {e}[/red]")
        
        return 0.0

    @lru_cache(maxsize=1000)
    def _get_rds_pricing(self, instance_class: str, engine: str = 'mysql') -> float:
        """Get RDS instance pricing directly from AWS Pricing API."""
        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine},
                ]
            )
            
            if response['PriceList']:
                price_data = json.loads(response['PriceList'][0])
                price = float(price_data['terms']['OnDemand'][list(price_data['terms']['OnDemand'].keys())[0]]['priceDimensions'][list(price_data['terms']['OnDemand'][list(price_data['terms']['OnDemand'].keys())[0]]['priceDimensions'].keys())[0]]['pricePerUnit']['USD'])
                return price
        except ClientError as e:
            console.print(f"[red]Error getting RDS pricing: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error getting RDS pricing: {e}[/red]")
        
        return 0.0

    @lru_cache(maxsize=1000)
    def _get_s3_pricing(self, storage_class: str = 'Standard') -> float:
        """Get S3 storage pricing directly from AWS Pricing API."""
        try:
            response = self.pricing_client.get_products(
                ServiceCode='AmazonS3',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'storageClass', 'Value': storage_class},
                ]
            )
            
            if response['PriceList']:
                price_data = json.loads(response['PriceList'][0])
                price = float(price_data['terms']['OnDemand'][list(price_data['terms']['OnDemand'].keys())[0]]['priceDimensions'][list(price_data['terms']['OnDemand'][list(price_data['terms']['OnDemand'].keys())[0]]['priceDimensions'].keys())[0]]['pricePerUnit']['USD'])
                return price
        except ClientError as e:
            console.print(f"[red]Error getting S3 pricing: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error getting S3 pricing: {e}[/red]")
        
        return 0.0

    def _estimate_ec2_cost(self, instance_type: str, os: str = 'Linux', tenancy: str = 'Shared') -> float:
        """Estimate EC2 instance cost."""
        hourly_price = self._get_ec2_pricing(instance_type, os, tenancy)
        monthly_cost = hourly_price * 24 * 30  # 30 days
        return monthly_cost

    def _estimate_rds_cost(self, instance_class: str, storage_gb: int = 20, engine: str = 'mysql') -> float:
        """Estimate RDS instance cost."""
        instance_price = self._get_rds_pricing(instance_class, engine)
        storage_price = storage_gb * 0.115  # Basic storage cost per GB
        monthly_cost = (instance_price * 24 * 30) + (storage_price * 30)  # 30 days
        return monthly_cost

    def _estimate_s3_cost(self, storage_gb: int = 100, storage_class: str = 'Standard') -> float:
        """Estimate S3 storage cost."""
        price_per_gb = self._get_s3_pricing(storage_class)
        monthly_cost = storage_gb * price_per_gb * 30  # 30 days
        return monthly_cost

    def estimate_costs(self, plan_path: Path) -> Dict[str, float]:
        """Estimate costs from Terraform plan."""
        try:
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
                
            costs = {
                'ec2': 0.0,
                'rds': 0.0,
                's3': 0.0
            }
            
            # Parse plan and estimate costs
            for resource in plan_data.get('resource_changes', []):
                if resource['type'] == 'aws_instance':
                    instance_type = resource['change']['after'].get('instance_type', 't2.micro')
                    costs['ec2'] += self._estimate_ec2_cost(instance_type)
                    
                elif resource['type'] == 'aws_db_instance':
                    instance_class = resource['change']['after'].get('instance_class', 'db.t2.micro')
                    storage_gb = resource['change']['after'].get('allocated_storage', 20)
                    costs['rds'] += self._estimate_rds_cost(instance_class, storage_gb)
                    
                elif resource['type'] == 'aws_s3_bucket':
                    storage_gb = 100  # Default estimate
                    costs['s3'] += self._estimate_s3_cost(storage_gb)
                    
            return costs
        except Exception as e:
            console.print(f"[red]Error estimating costs: {e}[/red]")
            return {'ec2': 0.0, 'rds': 0.0, 's3': 0.0}

    def get_optimization_suggestions(self, plan_path: Path) -> List[CostOptimization]:
        """Get cost optimization suggestions using Bedrock."""
        try:
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
                
            optimizations = []
            
            # Analyze resources for optimization opportunities
            for resource in plan_data.get('resource_changes', []):
                if resource['type'] == 'aws_instance':
                    instance_type = resource['change']['after'].get('instance_type', 't2.micro')
                    current_cost = self._estimate_ec2_cost(instance_type)
                    tags = resource['change']['after'].get('tags', {})
                    
                    # Enhanced prompt for EC2 analysis
                    prompt = f"""
                    As an AWS cost optimization expert, analyze this EC2 instance configuration and provide detailed optimization recommendations:

                    Instance Configuration:
                    - Instance Type: {instance_type}
                    - Current Cost: ${current_cost}/month
                    - Region: {self.region}
                    - Tags: {tags}
                    
                    Please analyze the following aspects:
                    1. Instance Type Optimization:
                       - Compare with similar instance types in the same family
                       - Consider ARM-based instances if applicable
                       - Evaluate burstable vs fixed performance instances
                       
                    2. Purchasing Options:
                       - Reserved Instance recommendations based on expected usage duration
                       - Spot Instance opportunities for fault-tolerant workloads
                       - Savings Plans analysis
                       
                    3. Resource Utilization:
                       - CPU and memory requirements based on workload
                       - Storage optimization opportunities
                       - Network performance considerations
                       
                    4. Region Optimization:
                       - Compare costs across different regions
                       - Consider latency requirements
                       - Evaluate data transfer costs
                       
                    5. Additional Considerations:
                       - Auto-scaling opportunities
                       - Instance scheduling for non-production workloads
                       - Storage optimization
                       
                    For each recommendation, provide:
                    1. Specific action items
                    2. Estimated cost savings
                    3. Implementation complexity (Low/Medium/High)
                    4. Potential risks or trade-offs
                    5. Required changes to the infrastructure
                    
                    Format the response as a structured analysis with clear recommendations and cost impact.
                    """
                    
                    response = self.bedrock.invoke_model(
                        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                        body=json.dumps({
                            "prompt": prompt,
                            "max_tokens": 2000,
                            "temperature": 0.7
                        })
                    )
                    
                    # Parse Bedrock response and create optimization suggestions
                    # This is a simplified example - you'd want to parse the response more carefully
                    optimizations.append(CostOptimization(
                        resource_type='EC2',
                        resource_id=resource['address'],
                        current_cost=current_cost,
                        suggested_cost=current_cost * 0.7,  # Example 30% savings
                        recommendation='Consider using spot instances for non-critical workloads'
                    ))
                    
                elif resource['type'] == 'aws_s3_bucket':
                    # Enhanced prompt for S3 analysis
                    prompt = f"""
                    As an AWS cost optimization expert, analyze this S3 bucket configuration and provide detailed optimization recommendations:

                    S3 Configuration:
                    - Storage Class: Standard
                    - Estimated Size: 100GB
                    - Region: {self.region}
                    - Tags: {resource['change']['after'].get('tags', {})}
                    
                    Please analyze the following aspects:
                    1. Storage Class Optimization:
                       - Evaluate usage patterns for different storage classes
                       - Consider Intelligent-Tiering for unknown access patterns
                       - Analyze cost benefits of Standard-IA vs One Zone-IA
                       
                    2. Lifecycle Management:
                       - Design optimal lifecycle policies
                       - Evaluate transition to Glacier/Deep Archive
                       - Consider object expiration rules
                       
                    3. Data Transfer Optimization:
                       - Analyze cross-region replication costs
                       - Evaluate CloudFront integration
                       - Consider S3 Transfer Acceleration
                       
                    4. Storage Optimization:
                       - Compression opportunities
                       - Deduplication possibilities
                       - Object versioning impact
                       
                    5. Additional Considerations:
                       - Access patterns and caching strategies
                       - Security and compliance requirements
                       - Backup and disaster recovery needs
                       
                    For each recommendation, provide:
                    1. Specific action items
                    2. Estimated cost savings
                    3. Implementation complexity (Low/Medium/High)
                    4. Potential risks or trade-offs
                    5. Required changes to the infrastructure
                    
                    Format the response as a structured analysis with clear recommendations and cost impact.
                    """
                    
                    response = self.bedrock.invoke_model(
                        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                        body=json.dumps({
                            "prompt": prompt,
                            "max_tokens": 2000,
                            "temperature": 0.7
                        })
                    )
                    
                    # Parse Bedrock response and create optimization suggestions
                    optimizations.append(CostOptimization(
                        resource_type='S3',
                        resource_id=resource['address'],
                        current_cost=self._estimate_s3_cost(),
                        suggested_cost=self._estimate_s3_cost(storage_class='Standard-IA'),
                        recommendation='Implement lifecycle policies to move infrequently accessed data to Standard-IA storage'
                    ))
                    
            return optimizations
        except Exception as e:
            console.print(f"[red]Error getting optimization suggestions: {e}[/red]")
            return []

    def display_costs(self, costs: Dict[str, float]):
        """Display estimated costs in a formatted table."""
        table = Table(title="Estimated Monthly Costs")
        table.add_column("Service", style="cyan")
        table.add_column("Cost (USD)", justify="right", style="green")
        
        for service, cost in costs.items():
            table.add_row(service.upper(), f"${cost:.2f}")
            
        total = sum(costs.values())
        table.add_row("Total", f"${total:.2f}", style="bold green")
        
        console.print(table)

    def display_optimizations(self, optimizations: List[CostOptimization]):
        """Display cost optimization suggestions with detailed analysis."""
        if not optimizations:
            console.print("[yellow]No optimization suggestions available.[/yellow]")
            return

        # Group optimizations by resource type
        grouped_optimizations = {}
        for opt in optimizations:
            if opt.resource_type not in grouped_optimizations:
                grouped_optimizations[opt.resource_type] = []
            grouped_optimizations[opt.resource_type].append(opt)

        # Display each resource type's optimizations
        for resource_type, opts in grouped_optimizations.items():
            console.print(f"\n[bold cyan]=== {resource_type} Optimizations ===[/bold cyan]")
            
            for opt in opts:
                # Main recommendation table
                main_table = Table(
                    title=f"Resource: {opt.resource_id}",
                    show_header=True,
                    header_style="bold magenta",
                    border_style="blue"
                )
                main_table.add_column("Metric", style="cyan")
                main_table.add_column("Value", style="green")
                
                main_table.add_row("Current Cost", f"${opt.current_cost:.2f}/month")
                main_table.add_row("Potential Savings", f"${opt.current_cost - opt.suggested_cost:.2f}/month")
                main_table.add_row("Savings Percentage", f"{((opt.current_cost - opt.suggested_cost) / opt.current_cost * 100):.1f}%")
                
                console.print(main_table)
                
                # Detailed analysis table
                analysis_table = Table(
                    show_header=True,
                    header_style="bold yellow",
                    border_style="yellow"
                )
                analysis_table.add_column("Category", style="cyan")
                analysis_table.add_column("Recommendation", style="green")
                analysis_table.add_column("Impact", style="yellow")
                analysis_table.add_column("Complexity", style="magenta")
                
                # Parse the recommendation string for structured display
                try:
                    analysis = json.loads(opt.recommendation)
                    for category, details in analysis.items():
                        analysis_table.add_row(
                            category,
                            details.get('action', 'N/A'),
                            details.get('impact', 'N/A'),
                            details.get('complexity', 'N/A')
                        )
                except json.JSONDecodeError:
                    analysis_table.add_row(
                        "General",
                        opt.recommendation,
                        "High",
                        "Medium"
                    )
                
                console.print("\n[bold yellow]Detailed Analysis:[/bold yellow]")
                console.print(analysis_table)
                
                # Additional considerations
                console.print("\n[bold green]Additional Considerations:[/bold green]")
                considerations_table = Table(show_header=False, box=None)
                considerations_table.add_column("Consideration", style="cyan")
                
                try:
                    considerations = json.loads(opt.recommendation).get('considerations', [])
                    for consideration in considerations:
                        considerations_table.add_row(f"• {consideration}")
                except (json.JSONDecodeError, AttributeError):
                    considerations_table.add_row("• Review implementation impact")
                    considerations_table.add_row("• Consider testing in non-production first")
                    considerations_table.add_row("• Monitor performance after changes")
                
                console.print(considerations_table)
                console.print("\n" + "="*80 + "\n")

    def export_optimizations(self, optimizations: List[CostOptimization], format: str = 'json', output_path: Optional[Path] = None) -> None:
        """Export optimization suggestions to various formats.
        
        Args:
            optimizations: List of CostOptimization objects
            format: Export format ('json', 'csv', 'yaml')
            output_path: Optional path to save the export file
        """
        if not optimizations:
            console.print("[yellow]No optimization suggestions to export.[/yellow]")
            return

        # Prepare data for export
        export_data = []
        for opt in optimizations:
            try:
                analysis = json.loads(opt.recommendation)
            except json.JSONDecodeError:
                analysis = {"General": {"action": opt.recommendation, "impact": "High", "complexity": "Medium"}}

            export_data.append({
                "resource_type": opt.resource_type,
                "resource_id": opt.resource_id,
                "current_cost": opt.current_cost,
                "suggested_cost": opt.suggested_cost,
                "potential_savings": opt.current_cost - opt.suggested_cost,
                "savings_percentage": ((opt.current_cost - opt.suggested_cost) / opt.current_cost * 100),
                "analysis": analysis
            })

        # Generate filename if not provided
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"cost_optimizations_{timestamp}.{format}")

        try:
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            elif format.lower() == 'csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'resource_type', 'resource_id', 'current_cost', 
                        'suggested_cost', 'potential_savings', 'savings_percentage'
                    ])
                    writer.writeheader()
                    for item in export_data:
                        writer.writerow({k: v for k, v in item.items() if k != 'analysis'})
            
            elif format.lower() == 'yaml':
                import yaml
                with open(output_path, 'w') as f:
                    yaml.dump(export_data, f, default_flow_style=False)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")

            console.print(f"[green]Successfully exported optimizations to {output_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error exporting optimizations: {e}[/red]") 