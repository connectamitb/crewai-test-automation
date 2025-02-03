# CrewAI Test Automation Dashboard

A web application that provides advanced code analysis and test automation capabilities using CrewAI and various testing agents.

## Key Features

1. **Authentication**
   - Google Sign-in integration using Firebase
   - Secure session management

2. **Test Agents Dashboard**
   - Manual Test Agent: Create and manage manual test cases
   - Automation Test Agent: Convert manual tests to Selenium scripts
   - Performance Test Agent: JMeter performance testing
   - Auto-Debugging Agent: Analyze failure logs
   - Self-Healing Locators: Auto-correct broken XPath
   - GenAI Test Case Agent: AI-powered test generation
   - Exploratory Testing Agent: UI change detection
   - Report Compilation Agent: Test analytics

3. **Code Analysis**
   - Integration with Cursor AI via SSH
   - Real-time code analysis capabilities
   - Debugging and optimization suggestions

## Routes

- `/`: Main dashboard page
- `/login`: Authentication page
- `/auth`: Authentication endpoint for Firebase
- `/analyze-code`: Code analysis endpoint using Cursor AI
- `/submit_requirement`: Endpoint for submitting test requirements

## Architecture

The application follows a client-server architecture:
1. Flask backend handling requests and business logic
2. Firebase for authentication
3. Cursor AI integration for code analysis
4. Bootstrap/Tailwind CSS for responsive UI
