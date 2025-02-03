from setuptools import setup, find_packages

setup(
    name="testai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "crewai==0.11.0",
        "langchain==0.1.0",
        "openai>=1.7.1",
        "flask==3.0.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "pydantic==2.5.2"
    ]
) 