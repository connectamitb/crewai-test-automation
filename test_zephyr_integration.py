import os
import json
import logging
from testai.agents.test_case_mapping import TestCaseMappingAgent, TestCaseOutput, TestCaseFormat

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_create_simple_test_case():
    """Test creating a simple test case in Zephyr Scale"""
    try:
        # Initialize the agent
        agent = TestCaseMappingAgent()

        # Create a minimal test case
        test_case = TestCaseOutput(
            title="Simple Login Test",
            description="Test basic login functionality",
            format=TestCaseFormat(
                given=["User is on the login page"],
                when=["User enters valid credentials"],
                then=["User is logged in successfully"],
                tags=["test", "login"],
                priority="Normal"  # Updated to use Normal priority
            )
        )

        # Convert to dict
        test_case_dict = test_case.model_dump()

        # Log the test case we're about to send
        logger.info("Test Case to be sent:")
        logger.info(json.dumps(test_case_dict, indent=2))

        # Attempt to store in Zephyr Scale
        result = agent._store_in_zephyr(test_case_dict)

        if result:
            logger.info("Successfully created test case in Zephyr Scale")
        else:
            logger.error("Failed to create test case in Zephyr Scale")

    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        raise

if __name__ == "__main__":
    test_create_simple_test_case()