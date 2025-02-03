import pytest
from testai.agents.manual_test_agent import ManualTestAgent, TestCase

@pytest.mark.asyncio
async def test_create_test_case():
    agent = ManualTestAgent()
    requirement = """
    As a user, I want to log in to the application 
    using my email and password so that I can access my account
    """
    
    test_case = await agent.create_test_case(requirement)
    
    assert isinstance(test_case, TestCase)
    assert test_case.title != ""
    assert len(test_case.steps) > 0
    assert len(test_case.expected_results) > 0 