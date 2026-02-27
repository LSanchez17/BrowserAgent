import asyncio
import argparse
import json

from agent.browser_agent import BrowserAgent

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LLM-powered browser that describes web pages"
    )
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help='URL to visit'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (invisible)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='qwen3:8b',
        help='Ollama model to use (default: qwen3:8b)'
    )
    parser.add_argument(
        '--ollama-url',
        type=str,
        default='http://localhost:11434',
        help='Ollama API URL (default: http://localhost:11434)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Optional: Save results to JSON file'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 BROWSER AGENT - Describe What You See")
    print("=" * 70)
    
    # Create and run browser agent
    async with BrowserAgent(
        ollama_url=args.ollama_url,
        model=args.model,
        headless=args.headless
    ) as agent:
        
        # Describe the page
        result = await agent.describe_page(args.url)
        
        # Print results
        print("\n" + "=" * 70)
        print("📊 RESULTS")
        print("=" * 70)
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"\nDescription:\n{result['description']}")
        
        # Save if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Saved to: {args.output}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
