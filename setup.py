from setuptools import setup, find_packages

setup(
    name="testai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "crewai>=0.14.1",
        "langchain>=0.1.0",
        "openai>=1.12.0",
        "flask==3.0.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "pydantic>=2.6.1",
        "pydantic-settings>=2.1.0",
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.5"
    ]
) 