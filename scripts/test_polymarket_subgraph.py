#!/usr/bin/env python3
"""
Test Polymarket Subgraph Connection
Diagnoses GraphQL query issues with Polymarket subgraph
"""

import asyncio
import aiohttp
import json

POLYMARKET_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/polymarket/matic-markets"

async def test_subgraph_queries():
    """Test different GraphQL queries to find working one"""
    
    queries = [
        ("Simple users query", """
        {
          users(first: 10) {
            id
          }
        }
        """),
        ("Users with volume", """
        {
          users(first: 10, orderBy: volumeTraded, orderDirection: desc) {
            id
            volumeTraded
          }
        }
        """),
        ("Check schema introspection", """
        {
          __schema {
            queryType {
              fields {
                name
                type {
                  name
                }
              }
            }
          }
        }
        """),
        ("Try different entity", """
        {
          markets(first: 5) {
            id
            question
          }
        }
        """),
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, query in queries:
            print(f"\n{'='*70}")
            print(f"Testing: {name}")
            print(f"{'='*70}")
            print(f"Query:\n{query.strip()}\n")
            
            try:
                async with session.post(
                    POLYMARKET_SUBGRAPH,
                    json={"query": query},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    print(f"Status: {response.status}")
                    data = await response.json()
                    
                    if 'errors' in data:
                        print("❌ GraphQL Errors:")
                        for err in data['errors']:
                            print(f"  - {err.get('message', str(err))}")
                            if 'locations' in err:
                                print(f"    Locations: {err['locations']}")
                            if 'path' in err:
                                print(f"    Path: {err['path']}")
                    elif 'data' in data:
                        print("✅ Success!")
                        if data['data']:
                            print(f"Response keys: {list(data['data'].keys())}")
                            # Show sample data
                            for key, value in data['data'].items():
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"\nSample {key} entry:")
                                    print(json.dumps(value[0], indent=2))
                                elif value:
                                    print(f"\n{key}: {json.dumps(value, indent=2)}")
                        else:
                            print("Empty data response")
                    else:
                        print(f"Unexpected response: {list(data.keys())}")
                        print(json.dumps(data, indent=2))
                        
            except Exception as e:
                print(f"❌ Request failed: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  POLYMARKET SUBGRAPH DIAGNOSTIC")
    print("="*70)
    asyncio.run(test_subgraph_queries())
    print("\n" + "="*70)
    print("  DIAGNOSTIC COMPLETE")
    print("="*70 + "\n")

