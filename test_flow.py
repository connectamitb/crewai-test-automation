from integrations.weaviate_integration import WeaviateIntegration
from weaviate.classes.query import MetadataQuery

def test_basic_flow():
    client = WeaviateIntegration()
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "User Login Test",
            "description": "Verify user login functionality with valid credentials",
            "steps": [
                "Navigate to login page",
                "Enter valid username and password",
                "Click login button"
            ],
            "expected_results": [
                "Login page loads successfully",
                "Credentials are accepted",
                "User is redirected to dashboard"
            ]
        },
        {
            "name": "Password Reset Test",
            "description": "Verify password reset functionality",
            "steps": [
                "Click forgot password link",
                "Enter registered email",
                "Submit reset request"
            ],
            "expected_results": [
                "Reset password page loads",
                "Reset email is sent",
                "User receives confirmation"
            ]
        }
    ]
    
    # Store test cases
    for test_case in test_cases:
        case_id = client.store_test_case(test_case)
        print(f"\nStored test case with ID: {case_id}")
        print(f"Name: {test_case['name']}")
    
    # Search for test cases
    print("\nSearching for login-related test cases:")
    results = client.search_test_cases("login authentication", limit=2)
    
    print("\nSearch Results:")
    for result in results:
        print(f"\nName: {result.properties['name']}")
        print(f"Description: {result.properties['description']}")
        print(f"Steps: {result.properties['steps']}")
        print(f"Distance: {result.metadata.distance}")
        print("-" * 50)

    client.close()

if __name__ == "__main__":
    test_basic_flow() 