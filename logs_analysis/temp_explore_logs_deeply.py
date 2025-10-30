#!/usr/bin/env python3
"""
Temporary Script: Deep Log Exploration
Explore OpenSearch logs to understand different fields and their meanings.
This will help build a generic natural language requirement processor.
"""

import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set
import pandas as pd
from opensearchpy import OpenSearch
import warnings
warnings.filterwarnings('ignore')

# OpenSearch connection configuration
OPENSEARCH_CONFIG = {
    "host": "os-dashboard.oneai.yo-digital.com",
    "port": 443,
    "username": "oneai_bharat",
    "password": "Z#Stp6$(qIyKaSGV",
    "index": "ia-platform-prod-*",
    "use_ssl": True,
    "verify_certs": False
}

def connect_to_opensearch():
    """Connect to OpenSearch cluster"""
    try:
        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_CONFIG['host'], 'port': OPENSEARCH_CONFIG['port']}],
            http_auth=(OPENSEARCH_CONFIG['username'], OPENSEARCH_CONFIG['password']),
            use_ssl=OPENSEARCH_CONFIG['use_ssl'],
            verify_certs=OPENSEARCH_CONFIG['verify_certs']
        )
        print("✅ Successfully connected to OpenSearch")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to OpenSearch: {e}")
        return None

def extract_all_fields_recursively(doc: Dict[str, Any], prefix: str = "", level: int = 0, max_depth: int = 10) -> Dict[str, Any]:
    """Recursively extract all fields from a document"""
    fields = {}
    
    if level > max_depth:
        return fields
    
    if isinstance(doc, dict):
        for key, value in doc.items():
            full_field_name = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Nested object
                nested_fields = extract_all_fields_recursively(value, full_field_name, level + 1, max_depth)
                fields.update(nested_fields)
                # Also store the object itself
                fields[full_field_name] = {
                    'type': 'object',
                    'level': level,
                    'sample_value': str(value)[:500] if value else None
                }
            elif isinstance(value, list):
                # Array
                if value and isinstance(value[0], dict):
                    # Array of objects - process each item
                    for i, item in enumerate(value[:5]):  # Limit to first 5
                        nested_fields = extract_all_fields_recursively(item, f"{full_field_name}[{i}]", level + 1, max_depth)
                        fields.update(nested_fields)
                else:
                    # Array of primitives
                    fields[full_field_name] = {
                        'type': 'array',
                        'level': level,
                        'sample_value': str(value[:10])[:500] if value else None,
                        'length': len(value)
                    }
            else:
                # Primitive value
                field_type = type(value).__name__
                fields[full_field_name] = {
                    'type': field_type,
                    'level': level,
                    'sample_value': str(value)[:500] if value is not None else None
                }
    
    return fields

def sample_documents_by_event_type(client, days_back: int = 4):
    """Sample documents by different event types to understand field patterns"""
    print("\n🔍 Sampling documents by event type...")
    
    # Use the date range that matches our previous successful queries
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # First, get all unique event types
    event_type_query = {
        "size": 0,
        "aggs": {
            "event_types": {
                "terms": {
                    "field": "event.keyword",
                    "size": 100
                }
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "event"}},
                    {"range": {
                        "@timestamp": {
                            "gte": start_date,
                            "lte": end_date
                        }
                    }}
                ]
            }
        }
    }
    
    try:
        response = client.search(
            index=OPENSEARCH_CONFIG['index'],
            body=event_type_query
        )
        
        event_types = response['aggregations']['event_types']['buckets']
        print(f"📊 Found {len(event_types)} unique event types")
        
        # Sample documents for each event type
        event_samples = {}
        
        for bucket in event_types[:30]:  # Top 30 event types
            event_type = bucket['key']
            count = bucket['doc_count']
            
            print(f"\n  📋 Event: {event_type} ({count} occurrences)")
            
            # Get sample documents for this event type
            # Try multiple query approaches
            sample_query = {
                "size": 3,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"event.keyword": event_type}},
                            {"range": {
                                "@timestamp": {
                                    "gte": start_date,
                                    "lte": end_date
                                }
                            }}
                        ]
                    }
                }
            }
            
            # Fallback queries if the above doesn't work
            fallback_queries = [
                {
                    "size": 3,
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"event": event_type}},
                                {"range": {
                                    "@timestamp": {
                                        "gte": start_date,
                                        "lte": end_date
                                    }}}
                            ]
                        }
                    }
                },
                {
                    "size": 3,
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"event": event_type}},
                                {"range": {
                                    "@timestamp": {
                                        "gte": start_date,
                                        "lte": end_date
                                    }}}
                            ]
                        }
                    }
                }
            ]
            
            samples = []
            query_worked = False
            
            # Try the main query
            for query_idx, query in enumerate([sample_query] + fallback_queries):
                try:
                    sample_response = client.search(
                        index=OPENSEARCH_CONFIG['index'],
                        body=query
                    )
                    
                    # Debug: Check response structure
                    if 'hits' in sample_response:
                        samples = sample_response['hits'].get('hits', [])
                        total = sample_response['hits'].get('total', {})
                        total_value = total.get('value', 0) if isinstance(total, dict) else total
                        
                        if samples:
                            print(f"    ✅ Got {len(samples)} sample documents (total: {total_value}) [query {query_idx+1}]")
                            # Print first sample structure for debugging
                            if samples and '_source' in samples[0]:
                                print(f"    Sample fields: {list(samples[0]['_source'].keys())[:10]}")
                            query_worked = True
                            break
                
                except Exception as e:
                    if query_idx < len(fallback_queries):
                        continue  # Try next query
                    else:
                        print(f"    ❌ Error with all queries: {e}")
            
            if not query_worked:
                print(f"    ⚠️  No samples returned after trying all queries")
            
            event_samples[event_type] = {
                'total_count': count,
                'samples': samples
            }
        
        return event_samples
        
    except Exception as e:
        print(f"❌ Error getting event types: {e}")
        return {}

def analyze_field_patterns(all_fields: Dict[str, Dict]) -> Dict[str, Any]:
    """Analyze field patterns to understand their meanings"""
    print("\n🔍 Analyzing field patterns...")
    
    field_analysis = {
        'total_fields': len(all_fields),
        'fields_by_type': defaultdict(list),
        'fields_by_level': defaultdict(list),
        'field_frequency': {},
        'completion_related': [],
        'conversation_related': [],
        'ab_test_related': [],
        'temporal_fields': [],
        'status_fields': [],
        'identifier_fields': [],
        'metadata_fields': []
    }
    
    # Keywords for categorization
    completion_keywords = [
        'resolved', 'unresolved', 'completion', 'status', 'handover',
        'ongoing', 'ended', 'closed', 'finished', 'outcome', 'result',
        'resolution', 'final', 'complete', 'abandon', 'success', 'fail'
    ]
    
    conversation_keywords = [
        'conversation', 'turn', 'chat', 'message', 'dialogue', 'session',
        'interaction', 'exchange'
    ]
    
    ab_test_keywords = [
        'ab', 'experiment', 'variant', 'test', 'bucket', 'treatment',
        'control', 'group'
    ]
    
    temporal_keywords = [
        'time', 'date', 'timestamp', 'created', 'updated', 'duration',
        'elapsed', 'start', 'end', 'when', 'ago'
    ]
    
    status_keywords = [
        'status', 'state', 'phase', 'stage', 'step', 'level', 'condition'
    ]
    
    identifier_keywords = [
        'id', 'uuid', 'guid', 'key', 'hash', 'token', 'reference'
    ]
    
    metadata_keywords = [
        'metadata', 'meta', 'info', 'details', 'context', 'environment',
        'tenant', 'channel', 'application', 'version', 'namespace'
    ]
    
    for field_name, field_info in all_fields.items():
        field_lower = field_name.lower()
        field_type = field_info.get('type', 'unknown')
        level = field_info.get('level', 0)
        
        # Categorize fields
        field_analysis['fields_by_type'][field_type].append(field_name)
        field_analysis['fields_by_level'][level].append(field_name)
        
        # Check for specific patterns
        if any(keyword in field_lower for keyword in completion_keywords):
            field_analysis['completion_related'].append(field_name)
        
        if any(keyword in field_lower for keyword in conversation_keywords):
            field_analysis['conversation_related'].append(field_name)
        
        if any(keyword in field_lower for keyword in ab_test_keywords):
            field_analysis['ab_test_related'].append(field_name)
        
        if any(keyword in field_lower for keyword in temporal_keywords):
            field_analysis['temporal_fields'].append(field_name)
        
        if any(keyword in field_lower for keyword in status_keywords):
            field_analysis['status_fields'].append(field_name)
        
        if any(keyword in field_lower for keyword in identifier_keywords):
            field_analysis['identifier_fields'].append(field_name)
        
        if any(keyword in field_lower for keyword in metadata_keywords):
            field_analysis['metadata_fields'].append(field_name)
    
    return field_analysis

def analyze_field_values(client, important_fields: List[str], sample_size: int = 100):
    """Analyze values for important fields to understand their meanings"""
    print("\n🔍 Analyzing field values...")
    
    start_date = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%dT00:00:00")
    end_date = datetime.now().strftime("%Y-%m-%dT23:59:59")
    
    field_value_analysis = {}
    
    for field in important_fields[:20]:  # Analyze top 20 fields
        print(f"\n  📋 Analyzing field: {field}")
        
        # Get unique values for this field
        try:
            # Try aggregation query
            agg_query = {
                "size": 0,
                "aggs": {
                    "field_values": {
                        "terms": {
                            "field": f"{field}.keyword",
                            "size": 50
                        }
                    }
                },
                "query": {
                    "bool": {
                        "must": [
                            {"exists": {"field": field}},
                            {"range": {
                                "@timestamp": {
                                    "gte": start_date,
                                    "lte": end_date
                                }
                            }}
                        ]
                    }
                }
            }
            
            response = client.search(
                index=OPENSEARCH_CONFIG['index'],
                body=agg_query
            )
            
            buckets = response['aggregations']['field_values']['buckets']
            
            field_value_analysis[field] = {
                'unique_values': len(buckets),
                'top_values': [(b['key'], b['doc_count']) for b in buckets[:10]],
                'total_docs': sum(b['doc_count'] for b in buckets)
            }
            
            print(f"    ✅ Found {len(buckets)} unique values")
            print(f"    Top 5 values: {[(v, c) for v, c in field_value_analysis[field]['top_values'][:5]]}")
            
        except Exception as e:
            # If aggregation fails, try sampling
            try:
                sample_query = {
                    "size": 50,
                    "query": {
                        "bool": {
                            "must": [
                                {"exists": {"field": field}},
                                {"range": {
                                    "@timestamp": {
                                        "gte": start_date,
                                        "lte": end_date
                                    }
                                }}
                            ]
                        }
                    }
                }
                
                response = client.search(
                    index=OPENSEARCH_CONFIG['index'],
                    body=sample_query
                )
                
                values = []
                for hit in response['hits']['hits']:
                    field_value = hit['_source'].get(field)
                    if field_value is not None:
                        values.append(str(field_value))
                
                value_counts = Counter(values)
                field_value_analysis[field] = {
                    'unique_values': len(value_counts),
                    'top_values': value_counts.most_common(10),
                    'total_docs': len(values),
                    'method': 'sampling'
                }
                
                print(f"    ✅ Sampled {len(values)} documents")
                print(f"    Top 5 values: {value_counts.most_common(5)}")
                
            except Exception as e2:
                print(f"    ❌ Error analyzing {field}: {e2}")
                field_value_analysis[field] = {'error': str(e2)}
    
    return field_value_analysis

def create_field_documentation(all_fields: Dict, field_analysis: Dict, field_values: Dict, event_samples: Dict) -> Dict[str, Any]:
    """Create comprehensive documentation of fields and their meanings"""
    print("\n📚 Creating field documentation...")
    
    documentation = {
        'timestamp': datetime.now().isoformat(),
        'total_fields_discovered': len(all_fields),
        'field_categories': {
            'completion_related': field_analysis['completion_related'],
            'conversation_related': field_analysis['conversation_related'],
            'ab_test_related': field_analysis['ab_test_related'],
            'temporal_fields': field_analysis['temporal_fields'],
            'status_fields': field_analysis['status_fields'],
            'identifier_fields': field_analysis['identifier_fields'],
            'metadata_fields': field_analysis['metadata_fields']
        },
        'fields_by_type': dict(field_analysis['fields_by_type']),
        'fields_by_level': dict(field_analysis['fields_by_level']),
        'field_value_analysis': field_values,
        'event_type_samples': {}
    }
    
    # Document event types and their typical fields
    for event_type, event_data in list(event_samples.items())[:20]:
        event_docs = []
        for sample in event_data['samples']:
            sample_fields = extract_all_fields_recursively(sample['_source'])
            event_docs.append({
                'conversationId': sample['_source'].get('conversationId'),
                'turnId': sample['_source'].get('turnId'),
                'fields': list(sample_fields.keys())[:20]  # Top 20 fields
            })
        
        documentation['event_type_samples'][event_type] = {
            'total_count': event_data['total_count'],
            'typical_fields': list(set([
                field for doc in event_docs 
                for field in doc['fields']
            ]))[:30]  # Top 30 unique fields
        }
    
    return documentation

def main():
    """Main function to explore logs deeply"""
    print("🚀 Deep Log Exploration for Field Understanding")
    print("=" * 70)
    
    # Connect to OpenSearch
    client = connect_to_opensearch()
    if not client:
        return
    
    # Step 1: Sample documents by event type
    event_samples = sample_documents_by_event_type(client, days_back=4)
    
    # Step 2: Extract all fields from sampled documents
    print("\n🔍 Extracting all fields from sampled documents...")
    all_fields = {}
    field_frequency = Counter()
    
    for event_type, event_data in event_samples.items():
        print(f"  Processing event type: {event_type} ({len(event_data.get('samples', []))} samples)")
        for sample in event_data.get('samples', []):
            if '_source' in sample:
                sample_fields = extract_all_fields_recursively(sample['_source'])
                for field_name, field_info in sample_fields.items():
                    if field_name not in all_fields:
                        all_fields[field_name] = field_info
                    field_frequency[field_name] += 1
    
    print(f"✅ Extracted {len(all_fields)} unique fields")
    
    # Step 3: Analyze field patterns
    field_analysis = analyze_field_patterns(all_fields)
    
    # Step 4: Analyze values for important fields
    important_fields = (
        field_analysis['completion_related'] +
        field_analysis['conversation_related'] +
        field_analysis['ab_test_related'] +
        field_analysis['status_fields'] +
        [field for field, _ in field_frequency.most_common(20)]
    )
    
    important_fields = list(set(important_fields))  # Remove duplicates
    
    field_values = analyze_field_values(client, important_fields)
    
    # Step 5: Create documentation
    documentation = create_field_documentation(
        all_fields, 
        field_analysis, 
        field_values, 
        event_samples
    )
    
    # Save documentation
    output_file = 'field_documentation.json'
    with open(output_file, 'w') as f:
        json.dump(documentation, f, indent=2, default=str)
    
    print(f"\n✅ Saved field documentation to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 EXPLORATION SUMMARY")
    print("=" * 70)
    print(f"Total fields discovered: {len(all_fields)}")
    print(f"Completion-related fields: {len(field_analysis['completion_related'])}")
    print(f"Conversation-related fields: {len(field_analysis['conversation_related'])}")
    print(f"A/B test-related fields: {len(field_analysis['ab_test_related'])}")
    print(f"Status fields: {len(field_analysis['status_fields'])}")
    print(f"Temporal fields: {len(field_analysis['temporal_fields'])}")
    print(f"Identifier fields: {len(field_analysis['identifier_fields'])}")
    
    print("\n🔍 Top 20 Most Frequent Fields:")
    for field, count in field_frequency.most_common(20):
        print(f"  - {field}: {count} occurrences")
    
    print("\n🔍 Completion-Related Fields:")
    for field in field_analysis['completion_related'][:10]:
        print(f"  - {field}")
    
    print("\n🔍 Conversation-Related Fields:")
    for field in field_analysis['conversation_related'][:10]:
        print(f"  - {field}")
    
    print("\n🔍 A/B Test-Related Fields:")
    for field in field_analysis['ab_test_related'][:10]:
        print(f"  - {field}")
    
    print("\n" + "=" * 70)
    print("✅ Deep log exploration complete!")
    print(f"Review {output_file} for detailed field documentation")

if __name__ == "__main__":
    main()
