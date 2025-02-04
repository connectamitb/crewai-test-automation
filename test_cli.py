import asyncio
from testai.agents.manual_test_agent import ManualTestAgent

async def main():
    agent = ManualTestAgent()
    requirement = """
    As a user, I want to log in to the application 
    using my email and password so that I can access my account
    """
    
    test_case = await agent.create_test_case(requirement)
    
if __name__ == "__main__":
    asyncio.run(main()) 