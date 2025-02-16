FLASK_SECRET_KEY=your_secret_key
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crewai-test-automation.git
cd crewai-test-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## API Documentation

### Test Cases

#### Create Test Case
`POST /api/v1/test-cases`
```json
{
  "requirement": "Test requirement text",
  "project_key": "TEST-123"
}
```

#### Search Test Cases
`GET /api/v1/test-cases/search?q=search_query`

#### Get Test Case
`GET /api/v1/test-cases/<case_id>`

## Project Structure
```
├── agents/              # AI agents for test operations
│   ├── nlp_parsing.py  # NLP processing agent
│   └── requirement_input.py  # Input processing agent
├── integrations/        # External service integrations
│   ├── models.py       # Data models
│   └── weaviate_integration.py  # Vector DB integration
├── routes/             # API route handlers
│   ├── health.py      # Health check endpoints
│   └── test_cases.py  # Test case management endpoints
├── static/             # Static assets
├── templates/          # HTML templates
└── tests/              # Unit and integration tests