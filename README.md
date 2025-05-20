# IAC CLI - Infrastructure as Code Command Line Tool

A powerful command-line tool for managing, validating, and optimizing Infrastructure as Code (IaC) using AI-powered features.

## Features

### Core Features
- **Terraform Validation**: Validate your Terraform configurations for syntax and best practices
- **AI-Powered Fixes**: Automatically fix validation errors using Amazon Bedrock
- **Code Generation**: Generate Terraform code from natural language descriptions
- **Cost Estimation**: Estimate infrastructure costs and get optimization suggestions
- **Version Control Integration**: Manage Git operations directly from the CLI
- **CI/CD Integration**: Create and manage GitHub Actions workflows
- **Real-Time Feedback**: Get live updates on validation, costs, and more
- **Interactive Mode**: User-friendly interactive command-line interface

### Cost Estimation & Optimization
- Estimate monthly costs for AWS resources (EC2, RDS, S3)
- Get cost optimization suggestions:
  - Spot instance recommendations for non-critical workloads
  - Instance size optimization
  - Storage class recommendations
  - RDS instance optimization
  - S3 lifecycle policy suggestions
- View potential cost savings and implementation recommendations

### Version Control Features
- Git status monitoring
- Branch management
- Commit and push changes
- Pull request creation
- Diff viewing
- Rich formatting for better visibility

### CI/CD Integration
- Pre-configured GitHub Actions workflows:
  - Terraform validation and plan
  - Security scanning with tfsec and Checkov
  - Cost estimation and optimization
- Workflow management and customization
- Automated testing and validation

### Real-Time Feedback
- Live validation updates
- Real-time cost estimation
- Live plan generation
- Security scan progress
- Git status monitoring
- Rich terminal UI with progress indicators

### Interactive Mode
- Command-line interface with auto-completion
- Interactive prompts for all operations
- Rich formatting and tables
- Built-in help system
- Git operations integration
- Cost estimation and optimization

## Installation

```bash
pip install iac-cli
```

## Usage

### Basic Commands

```bash
# Validate Terraform files
iac-cli validate path/to/terraform.tf

# Fix validation errors
iac-cli fix path/to/terraform.tf

# Generate Terraform code
iac-cli generate "Create an EC2 instance with a security group" output.tf

# Estimate costs
iac-cli estimate-costs path/to/terraform.tf --optimize

# Git operations
iac-cli git status
iac-cli git commit
iac-cli git pr

# CI/CD management
iac-cli cicd list
iac-cli cicd create

# Start interactive mode
iac-cli interactive
```

### Cost Optimization

```bash
# Get cost estimates with optimization suggestions
iac-cli estimate-costs path/to/terraform.tf --optimize

# Live cost monitoring
iac-cli estimate-costs path/to/terraform.tf --live
```

### Real-Time Feedback

```bash
# Live validation
iac-cli validate path/to/terraform.tf --live

# Live plan generation
iac-cli plan path/to/terraform.tf --live

# Live security scanning
iac-cli security path/to/terraform.tf --live
```

## CLI Usage Example

Here's a complete example of using the CLI to analyze and optimize your AWS infrastructure costs:

```bash
# Initialize the CLI with your AWS region
iac-cli init --region us-east-1

# Analyze a Terraform plan file
iac-cli analyze-costs terraform.tfplan
```

Example output:
```
🔍 Analyzing infrastructure costs...

=== Cost Analysis Report ===
┌─────────┬────────────┬──────────────┐
│ Service │ Current    │ Optimized    │
├─────────┼────────────┼──────────────┤
│ EC2     │ $1,200.00  │ $840.00      │
│ RDS     │ $500.00    │ $350.00      │
│ S3      │ $300.00    │ $150.00      │
├─────────┼────────────┼──────────────┤
│ Total   │ $2,000.00  │ $1,340.00    │
└─────────┴────────────┴──────────────┘

Potential Monthly Savings: $660.00 (33.0%)

=== Detailed Recommendations ===

1. EC2 Instance (i-1234567890abcdef0)
   Current: t3.xlarge ($400/month)
   Recommended: t3.large ($200/month)
   Savings: $200/month (50%)
   Impact: High
   Complexity: Low
   Action: Downsize instance type

2. RDS Instance (db-1234567890abcdef0)
   Current: db.t3.large ($500/month)
   Recommended: db.t3.medium ($350/month)
   Savings: $150/month (30%)
   Impact: Medium
   Complexity: Medium
   Action: Optimize instance size and enable auto-scaling

3. S3 Bucket (my-bucket)
   Current: Standard Storage ($300/month)
   Recommended: Intelligent-Tiering ($150/month)
   Savings: $150/month (50%)
   Impact: Low
   Complexity: Low
   Action: Implement lifecycle policies

=== Implementation Steps ===

1. EC2 Changes:
   • Create new t3.large instance
   • Test application performance
   • Migrate workload
   • Terminate old instance

2. RDS Changes:
   • Enable auto-scaling
   • Modify instance type
   • Update connection strings
   • Monitor performance

3. S3 Changes:
   • Enable Intelligent-Tiering
   • Configure lifecycle rules
   • Monitor storage costs

Would you like to:
1. Export recommendations to JSON/CSV/YAML
2. Generate implementation plan
3. Schedule optimization tasks
4. Exit

Choice [1-4]: 
```

You can also use specific commands for different aspects of cost optimization:

```bash
# Get only EC2 recommendations
iac-cli analyze-costs terraform.tfplan --service ec2

# Get recommendations with implementation steps
iac-cli analyze-costs terraform.tfplan --with-steps

# Export recommendations to a file
iac-cli analyze-costs terraform.tfplan --export json --output recommendations.json

# Get real-time cost monitoring
iac-cli monitor-costs terraform.tfplan --live
```

The CLI provides interactive prompts and rich formatting to make it easy to understand and implement cost optimizations. You can also integrate it into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Cost Analysis
on: [pull_request]

jobs:
  analyze-costs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run cost analysis
        run: |
          iac-cli analyze-costs terraform.tfplan
          iac-cli analyze-costs terraform.tfplan --export json --output cost-report.json
      - name: Upload cost report
        uses: actions/upload-artifact@v2
        with:
          name: cost-report
          path: cost-report.json
```

## Development

### Prerequisites
- Python 3.8 or higher
- AWS credentials configured
- Git installed
- GitHub CLI installed (for PR features)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/iac-cli.git
cd iac-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License

## Acknowledgments

- [Terraform](https://www.terraform.io/)
- [Amazon Bedrock](https://aws.amazon.com/bedrock/)
- [Typer](https://typer.tiangolo.com/)
- [Rich](https://github.com/Textualize/rich)

# AWS Infrastructure Cost Optimizer

A powerful CLI tool that analyzes your AWS infrastructure and provides intelligent cost optimization recommendations using AWS Pricing API and Amazon Bedrock.

## Features

- Real-time cost estimation using AWS Pricing API
- Intelligent optimization suggestions using Amazon Bedrock
- Support for multiple AWS services (EC2, RDS, S3)
- Detailed cost analysis and recommendations
- Export capabilities (JSON, CSV, YAML)

## Installation

```bash
pip install aws-cost-optimizer
```

## Usage

### Basic Cost Estimation

```python
from iac_cli.cost_estimator import CostEstimator

# Initialize the cost estimator
estimator = CostEstimator(region_name="us-east-1")

# Estimate costs from a Terraform plan
costs = estimator.estimate_costs("terraform.tfplan")
estimator.display_costs(costs)
```

Example output:
```
Estimated Monthly Costs
┌─────────┬────────────┐
│ Service │ Cost (USD) │
├─────────┼────────────┤
│ EC2     │ $100.00    │
│ RDS     │ $50.00     │
│ S3      │ $25.00     │
├─────────┼────────────┤
│ Total   │ $175.00    │
└─────────┴────────────┘
```

### Cost Optimization Analysis

```python
# Get optimization suggestions
optimizations = estimator.get_optimization_suggestions("terraform.tfplan")
estimator.display_optimizations(optimizations)
```

Example output:
```
=== EC2 Optimizations ===
Resource: aws_instance.web_server
┌───────────────┬──────────────┐
│ Metric        │ Value        │
├───────────────┼──────────────┤
│ Current Cost  │ $100.00/month│
│ Potential     │ $30.00/month │
│ Savings       │ 30.0%        │
└───────────────┴──────────────┘

Detailed Analysis:
┌──────────────┬──────────────┬────────┬──────────┐
│ Category     │ Recommendation│ Impact │ Complexity│
├──────────────┼──────────────┼────────┼──────────┤
│ Instance Type│ Use t3.medium │ High   │ Low      │
│ Purchasing   │ Use Reserved  │ High   │ Medium   │
└──────────────┴──────────────┴────────┴──────────┘

Additional Considerations:
• Review implementation impact
• Consider testing in non-production first
• Monitor performance after changes
```

### Exporting Results

```python
# Export to JSON
estimator.export_optimizations(optimizations, format='json')

# Export to CSV
estimator.export_optimizations(optimizations, format='csv')

# Export to YAML
estimator.export_optimizations(optimizations, format='yaml')
```

Example JSON output:
```json
[
  {
    "resource_type": "EC2",
    "resource_id": "aws_instance.web_server",
    "current_cost": 100.00,
    "suggested_cost": 70.00,
    "potential_savings": 30.00,
    "savings_percentage": 30.0,
    "analysis": {
      "Instance Type": {
        "action": "Use t3.medium",
        "impact": "High",
        "complexity": "Low"
      },
      "Purchasing": {
        "action": "Use Reserved Instances",
        "impact": "High",
        "complexity": "Medium"
      }
    }
  }
]
```

## Supported Services

- **EC2**: Instance type optimization, purchasing options, resource utilization
- **RDS**: Instance class optimization, storage optimization, backup strategies
- **S3**: Storage class optimization, lifecycle policies, data transfer optimization

## Requirements

- Python 3.8+
- AWS CLI configured with appropriate permissions
- Access to AWS Pricing API
- Access to Amazon Bedrock

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Error Handling Examples

The CLI provides clear error messages and recovery suggestions. Here are some common scenarios:

### Invalid AWS Credentials

```bash
$ iac-cli analyze-costs terraform.tfplan
```

```
❌ Error: AWS credentials not found or invalid
   Please ensure you have valid AWS credentials configured.

   You can configure credentials by:
   1. Running 'aws configure'
   2. Setting environment variables:
      export AWS_ACCESS_KEY_ID=your_access_key
      export AWS_SECRET_ACCESS_KEY=your_secret_key
   3. Using AWS SSO:
      aws sso login

   Would you like to:
   1. Configure AWS credentials now
   2. Use a different profile
   3. Exit

   Choice [1-3]: 
```

### Invalid Terraform Plan File

```bash
$ iac-cli analyze-costs invalid.tfplan
```

```
❌ Error: Invalid Terraform plan file
   The file 'invalid.tfplan' is not a valid Terraform plan.

   Possible issues:
   • File is corrupted
   • File is not a Terraform plan
   • File permissions are incorrect

   Would you like to:
   1. Generate a new Terraform plan
   2. Select a different file
   3. Exit

   Choice [1-3]: 
```

### API Rate Limiting

```bash
$ iac-cli analyze-costs terraform.tfplan
```

```
⚠️ Warning: AWS API rate limit reached
   The AWS Pricing API is currently rate limited.
   Retrying in 5 seconds...

   Progress: [████████░░░░] 80%
   Estimated time remaining: 2 minutes

   Would you like to:
   1. Continue waiting
   2. Save progress and resume later
   3. Cancel analysis

   Choice [1-3]: 
```

### Insufficient IAM Permissions

```bash
$ iac-cli analyze-costs terraform.tfplan
```

```
❌ Error: Insufficient IAM permissions
   Missing required permissions:
   - pricing:GetProducts
   - ec2:DescribeInstances
   - rds:DescribeDBInstances

   Required IAM Policy:
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "pricing:GetProducts",
           "ec2:DescribeInstances",
           "rds:DescribeDBInstances"
         ],
         "Resource": "*"
       }
     ]
   }

   Would you like to:
   1. View required permissions
   2. Generate IAM policy
   3. Exit

   Choice [1-3]: 
```

### Network Connectivity Issues

```bash
$ iac-cli analyze-costs terraform.tfplan
```

```
❌ Error: Network connectivity issue
   Unable to connect to AWS services.

   Diagnostics:
   • AWS API endpoint: api.pricing.us-east-1.amazonaws.com
   • Status: Connection timeout
   • Last successful connection: 5 minutes ago

   Possible solutions:
   1. Check your internet connection
   2. Verify AWS region is correct
   3. Check VPN/proxy settings
   4. Try a different region

   Would you like to:
   1. Retry connection
   2. Switch region
   3. Run in offline mode
   4. Exit

   Choice [1-4]: 
```

### Invalid Resource Configuration

```bash
$ iac-cli analyze-costs terraform.tfplan
```

```
⚠️ Warning: Invalid resource configuration detected
   Resource: aws_instance.web_server
   Issue: Instance type 't3.micro' is too small for the workload

   Current configuration:
   • Instance type: t3.micro
   • Memory: 1 GB
   • CPU: 2 vCPUs

   Required resources:
   • Memory: 4 GB minimum
   • CPU: 4 vCPUs minimum

   Would you like to:
   1. View detailed analysis
   2. Get optimization suggestions
   3. Ignore warning
   4. Exit

   Choice [1-4]: 
```

### Recovery and Retry Mechanisms

The CLI includes automatic recovery mechanisms:

```bash
$ iac-cli analyze-costs terraform.tfplan --retry 3 --timeout 300
```

```
🔄 Attempting to recover from error...

Progress:
[██████████░░] 90%
Retry attempt: 2/3
Time remaining: 45 seconds

Recovery steps:
1. Validating AWS credentials
2. Checking API endpoints
3. Verifying resource configurations
4. Testing connectivity

Status: Recovered successfully
Continuing analysis...
```

These error handling features help users:
- Understand what went wrong
- Get specific recovery steps
- Make informed decisions
- Automatically recover when possible
- Save progress and resume later 
