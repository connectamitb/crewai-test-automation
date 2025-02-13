import asyncio
from testai.integrations.weaviate_integration import WeaviateIntegration

async def main():
    weaviate = WeaviateIntegration()
    
    while True:
        query = input("\nEnter search query (or 'q' to quit): ")
        if query.lower() == 'q':
            break
            
        results = weaviate.search_by_requirement(query)
        
        print("\nFound Test Cases:")
        print("================")
        
        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. {result['name']}")
            print(f"Requirement: {result['requirement']}")
            print("\nGherkin:")
            print(result['gherkin'])
            print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 