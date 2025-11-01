#!/usr/bin/env python3
"""End-to-end integration test for the streaming API endpoint.

This test validates the complete streaming API flow:
1. Index discovery
2. Schema discovery  
3. Natural language parsing
4. Query building
5. All intermediate steps are validated

The streaming API is at http://localhost:8000/query/stream

Based on logs_analysis documentation to create realistic test queries.

Usage:
    # Start the API server first:
    # uvicorn nlap.main:app --host 0.0.0.0 --port 8000
    
    python tests/integration/test_streaming_api_e2e.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import httpx

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


API_BASE_URL = "http://localhost:8000"


class StreamingAPITester:
    """Test harness for the streaming API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.stream_endpoint = f"{base_url}/query/stream"
        self.test_results: List[Dict] = []
        
    async def test_connection(self) -> bool:
        """Test if the API is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except Exception as e:
            print(f"✗ Cannot connect to API at {self.base_url}: {e}")
            return False
    
    async def stream_query(
        self, 
        query: str,
        index_names: Optional[List[str]] = None,
        discover_fields: bool = True,
        size: Optional[int] = None,
        from_: int = 0
    ) -> Dict:
        """Send a query to the streaming API and collect all events."""
        events = []
        errors = []
        
        payload = {
            "query": query,
            "discover_fields": discover_fields,
            "from": from_,
        }
        
        if index_names:
            payload["index_names"] = index_names
        if size:
            payload["size"] = size
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    self.stream_endpoint,
                    json=payload,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        return {
                            "status": "error",
                            "http_status": response.status_code,
                            "error": error_text.decode(),
                            "events": [],
                        }
                    
                    buffer = ""
                    async for chunk in response.aiter_bytes():
                        buffer += chunk.decode("utf-8")
                        
                        # Process complete SSE messages
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)
                            
                            if message.startswith("data: "):
                                data_str = message[6:]  # Remove "data: " prefix
                                try:
                                    event_data = json.loads(data_str)
                                    events.append(event_data)
                                    
                                    # Check for errors
                                    if event_data.get("type") == "error":
                                        errors.append(event_data.get("data", {}))
                                except json.JSONDecodeError:
                                    pass
                    
                    # Process any remaining buffer
                    if buffer.strip():
                        if buffer.startswith("data: "):
                            try:
                                data_str = buffer[6:]
                                event_data = json.loads(data_str)
                                events.append(event_data)
                                if event_data.get("type") == "error":
                                    errors.append(event_data.get("data", {}))
                            except json.JSONDecodeError:
                                pass
                
                return {
                    "status": "error" if errors else "success",
                    "events": events,
                    "errors": errors,
                }
                
        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": "Request timeout",
                "events": events,
                "errors": errors,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "events": events,
                "errors": errors,
            }
    
    def validate_streaming_response(self, result: Dict) -> Dict:
        """Validate the streaming response structure."""
        validation = {
            "has_initialization": False,
            "has_index_discovery": False,
            "has_schema_discovery": False,
            "has_parsing": False,
            "has_query_building": False,
            "has_completion": False,
            "has_errors": False,
            "schema_discovered": None,
            "parsed_query": None,
            "opensearch_query": None,
            "event_sequence": [],
        }
        
        for event in result.get("events", []):
            event_type = event.get("type")
            data = event.get("data", {})
            
            validation["event_sequence"].append(event_type)
            
            if event_type == "status":
                step = data.get("step")
                if step == "initialization":
                    validation["has_initialization"] = True
                elif step == "index_discovery":
                    validation["has_index_discovery"] = True
                elif step == "parsing":
                    validation["has_parsing"] = True
                elif step == "query_building":
                    validation["has_query_building"] = True
                    
            elif event_type == "schema_discovered":
                validation["has_schema_discovery"] = True
                validation["schema_discovered"] = data.get("schema", {})
                
            elif event_type == "parsed":
                validation["has_parsing"] = True
                validation["parsed_query"] = data.get("parsed_query", {})
                
            elif event_type == "query_built":
                validation["has_query_building"] = True
                validation["opensearch_query"] = data.get("opensearch_query", {})
                
            elif event_type == "complete":
                validation["has_completion"] = True
                
            elif event_type == "error":
                validation["has_errors"] = True
                
            elif event_type == "warning":
                # Warnings are not errors
                pass
        
        return validation
    
    async def run_test_case(
        self,
        test_name: str,
        query: str,
        index_names: Optional[List[str]] = None,
        discover_fields: bool = True,
        expected_steps: Optional[List[str]] = None,
    ) -> Dict:
        """Run a single test case."""
        print(f"\n{'='*80}")
        print(f"Test: {test_name}")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        # Stream the query
        print("Sending query to streaming API...")
        result = await self.stream_query(
            query=query,
            index_names=index_names,
            discover_fields=discover_fields,
        )
        
        # Validate response
        validation = self.validate_streaming_response(result)
        
        # Print results
        print(f"Status: {result['status']}")
        print(f"Total events: {len(result['events'])}")
        
        # Print event sequence
        print(f"\nEvent Sequence:")
        for i, event in enumerate(result["events"], 1):
            event_type = event.get("type")
            data = event.get("data", {})
            
            if event_type == "status":
                step = data.get("step", "unknown")
                message = data.get("message", "")
                print(f"  {i}. [{event_type}] Step: {step} - {message}")
            elif event_type == "schema_discovered":
                schema = data.get("schema", {})
                total_fields = schema.get("total_fields", 0)
                index_name = schema.get("index_name", "unknown")
                print(f"  {i}. [{event_type}] Schema discovered for {index_name}: {total_fields} fields")
            elif event_type == "parsed":
                parsed = data.get("parsed_query", {})
                intent = parsed.get("intent", {}).get("category", "unknown")
                confidence = parsed.get("confidence", 0)
                index_names_parsed = parsed.get("index_names", [])
                print(f"  {i}. [{event_type}] Intent: {intent}, Confidence: {confidence:.2f}, Indices: {index_names_parsed}")
                if parsed.get("date_range"):
                    date_range = parsed["date_range"]
                    print(f"      Date range: {date_range.get('start_date')} to {date_range.get('end_date')}")
            elif event_type == "query_built":
                metadata = data.get("metadata", {})
                indices = metadata.get("index_names", [])
                has_aggs = metadata.get("has_aggregations", False)
                print(f"  {i}. [{event_type}] Indices: {indices}, Has aggregations: {has_aggs}")
            elif event_type == "complete":
                summary = data.get("summary", {})
                print(f"  {i}. [{event_type}] {data.get('message', 'Complete')}")
                print(f"      Original query: {summary.get('original_query', 'N/A')}")
            elif event_type == "error":
                error_data = data
                print(f"  {i}. [{event_type}] Error: {error_data.get('message', 'Unknown error')}")
            elif event_type == "warning":
                warning_data = data
                print(f"  {i}. [{event_type}] Warning: {warning_data.get('message', 'Unknown warning')}")
            else:
                print(f"  {i}. [{event_type}] {json.dumps(data, indent=2)[:100]}...")
        
        # Validate steps
        print(f"\nValidation:")
        print(f"  ✓ Initialization: {validation['has_initialization']}")
        print(f"  ✓ Index discovery: {validation['has_index_discovery']}")
        print(f"  ✓ Schema discovery: {validation['has_schema_discovery']}")
        print(f"  ✓ Parsing: {validation['has_parsing']}")
        print(f"  ✓ Query building: {validation['has_query_building']}")
        print(f"  ✓ Completion: {validation['has_completion']}")
        print(f"  ✗ Errors: {validation['has_errors']}")
        
        # Store test result
        test_result = {
            "test_name": test_name,
            "query": query,
            "status": result["status"],
            "event_count": len(result["events"]),
            "validation": validation,
            "errors": result.get("errors", []),
            "has_all_steps": all([
                validation["has_initialization"],
                validation["has_parsing"],
                validation["has_query_building"],
                validation["has_completion"],
            ]),
        }
        
        self.test_results.append(test_result)
        return test_result


async def main():
    """Run all test cases."""
    print("=" * 80)
    print("Streaming API End-to-End Test Suite")
    print("=" * 80)
    print()
    
    tester = StreamingAPITester()
    
    # Test connection
    print("Testing API connection...")
    if not await tester.test_connection():
        print("✗ API is not running. Please start the API server first:")
        print("  uvicorn nlap.main:app --host 0.0.0.0 --port 8000")
        return False
    print("✓ API is running")
    print()
    
    # Test cases based on logs_analysis.md
    test_cases = [
        {
            "name": "A/B Test Variant Query",
            "query": "show me all documents with AB experiment variant for the last 7 days",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Response Status Query",
            "query": "find all responses with status RESOLVED from last week",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Event Type Aggregation",
            "query": "count documents by event type for the last 4 days",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Date Range Query",
            "query": "show me all documents from August 2025",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Agent Handover Query",
            "query": "find all conversations that were handed over to agent in last month",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "LLM Completion Metrics",
            "query": "show me LLM completion events with response time greater than 1000ms",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Function Call Status",
            "query": "find all function calls that failed in the last week",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Completion Status Distribution",
            "query": "count responses grouped by response status for last month",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": True,
        },
        {
            "name": "Query Without Index Names",
            "query": "find all RESPONSE_RETURNED events from last week",
            "index_names": None,  # Let API discover indices
            "discover_fields": True,
        },
        {
            "name": "Query Without Schema Discovery",
            "query": "show me all documents from last 3 days",
            "index_names": ["ia-platform-prod-*"],
            "discover_fields": False,
        },
    ]
    
    # Run all test cases
    print(f"Running {len(test_cases)} test cases...\n")
    
    for test_case in test_cases:
        await tester.run_test_case(
            test_name=test_case["name"],
            query=test_case["query"],
            index_names=test_case.get("index_names"),
            discover_fields=test_case.get("discover_fields", True),
        )
        await asyncio.sleep(0.5)  # Small delay between tests
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print()
    
    total_tests = len(tester.test_results)
    success_tests = sum(1 for r in tester.test_results if r["status"] == "success")
    error_tests = sum(1 for r in tester.test_results if r["status"] == "error")
    complete_tests = sum(1 for r in tester.test_results if r.get("has_all_steps", False))
    
    print(f"Total tests: {total_tests}")
    print(f"✓ Successful: {success_tests}")
    print(f"✗ Failed: {error_tests}")
    print(f"✓ Complete flow (all steps): {complete_tests}")
    print()
    
    # Print detailed results
    print("Detailed Results:")
    for result in tester.test_results:
        status_icon = "✓" if result["status"] == "success" else "✗"
        complete_icon = "✓" if result.get("has_all_steps") else "✗"
        print(f"  {status_icon} {result['test_name']}")
        print(f"    Query: {result['query']}")
        print(f"    Events: {result['event_count']}")
        print(f"    All steps: {complete_icon}")
        if result.get("errors"):
            print(f"    Errors: {len(result['errors'])}")
        print()
    
    return error_tests == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


