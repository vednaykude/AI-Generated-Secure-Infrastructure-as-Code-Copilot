from setuptools import setup, find_packages

setup(
    name="iac-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.7.0",
        "python-hcl2>=4.3.2",
        "boto3>=1.34.0",
        "openai>=1.12.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.6.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "ruff>=0.2.1",
            "pre-commit>=3.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "iac-cli=iac_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered Infrastructure as Code validation and fixing tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/iac-cli",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 