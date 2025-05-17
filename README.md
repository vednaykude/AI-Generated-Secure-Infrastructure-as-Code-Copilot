# Cloud Security AI Review Bot 🛡️

An AI-powered security review system for Infrastructure as Code (IaC) that automatically analyzes and suggests fixes for security issues in your infrastructure code.

## Features 🌟

- 🧠 **Natural Language to Terraform**: Generate secure Terraform configurations from natural language descriptions
- ✅ **LLM Security Review**: AI-powered analysis of security posture with detailed explanations
- 🔍 **IaC Static Analysis**: Integrated Checkov/tfsec scanning for security misconfigurations
- 🛠️ **Automatic Fix Suggestions**: AI-generated patches for identified security issues
- 🧑‍💻 **GitHub Integration**: Automated PR reviews with inline comments and fix suggestions
- 📘 **Pre-Deployment Reports**: Comprehensive security summaries and review status

## Prerequisites 📋

- Python 3.8+
- GitHub account and repository access
- OpenAI API key
- Checkov installed

## Quick Start 🚀

1. Clone the repository:
```bash
git clone https://github.com/vednaykude/AI-Generated-Secure-Infrastructure-as-Code-Copilot.git
cd AI-Generated-Secure-Infrastructure-as-Code-Copilot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
DEBUG=False
ENVIRONMENT=development
MIN_SEVERITY_LEVEL=LOW
AUTO_FIX_ENABLED=True
```

4. Add the GitHub Action to your repository:
The `.github/workflows/security-review.yml` file is already included in the repository.

## Architecture 🏗️

The application consists of several key components:

1. **GitHub Integration**
   - Monitors PRs for infrastructure code changes
   - Triggers security analysis pipeline

2. **AI Reviewer Bot**
   - Runs static analysis (Checkov/tfsec)
   - Generates AI-powered explanations and fixes
   - Posts inline PR comments and suggestions

3. **Security Report Generator**
   - Creates comprehensive security summaries
   - Provides actionable insights and recommendations

## Configuration ⚙️

Configure the application by modifying `config.yaml`:

```yaml
github:
  webhook_secret: "your-webhook-secret"
  app_id: "your-app-id"

openai:
  model: "gpt-4-turbo-preview"
  temperature: 0.7

checkov:
  skip_frameworks: []
  check_ids: []
```

## Contributing 🤝

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 💬

For support, please open an issue in the GitHub repository or contact the maintainer at ved.naykude@gmail.com. 