#!/usr/bin/env python3
"""
OpenSearch Field Explorer - Temporary script to understand log structure
Explores different event types and their field meanings
"""

import subprocess
import sys
import json
from datetime import datetime, timedelta

def install_requirements():
    """Install required packages"""
    try:
        import opensearchpy
    except ImportError:
        print(f"Installing opensearch-py...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'opensearch-py'])

install_requirements()

from opensearchpy import OpenSearch

# OpenSearch configuration
OPENSEARCH_CONFIG = {
    "host": "os-dashboard.oneai.yo-digital.com",
    "port": 443,
    "username": "oneai_bharat", 
    "password": "Z#Stp6$(qIyKaSGV",
    "index": "ia-platform-prod-*",
    "use_ssl": True,
    "verify_certs": True
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
        print("✅ Connected to OpenSearch successfully\n")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to OpenSearch: {e}")
        return None

def get_all_event_types(client):
    """Get all unique event types in the index"""
    print("=" * 70)
    print("📊 ALL EVENT TYPES IN THE INDEX")
    print("=" * 70)
    
    query = {
        "size": 0,
        "aggs": {
            "event_types": {
                "terms": {
                    "field": "event.keyword",
                    "size": 100
                }
            }
        }
    }
    
    try:
        response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
        buckets = response['aggregations']['event_types']['buckets']
        
        print(f"Found {len(buckets)} unique event types:\n")
        for i, bucket in enumerate(buckets, 1):
            print(f"{i:3}. {bucket['key']:50} - {bucket['doc_count']:,} events")
        
        return buckets
    except Exception as e:
        print(f"❌ Error getting event types: {e}")
        return []

def explore_event_structure(client, event_name, num_samples=3):
    """Explore the structure of a specific event type"""
    print("\n" + "=" * 70)
    print(f"🔍 EXPLORING EVENT TYPE: {event_name}")
    print("=" * 70)
    
    query = {
        "size": num_samples,
        "query": {
            "bool": {
                "should": [
                    {"term": {"event": event_name}},
                    {"term": {"event.keyword": event_name}},
                    {"match": {"event": event_name}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}]
    }
    
    try:
        response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
        hits = response['hits']['hits']
        
        if not hits:
            print(f"No documents found for event: {event_name}")
            return None
        
        print(f"\n📋 Sample documents ({num_samples} most recent):")
        print("-" * 70)
        
        all_fields = set()
        for i, hit in enumerate(hits, 1):
            source = hit['_source']
            all_fields.update(source.keys())
            
            print(f"\n--- Sample {i} ---")
            print(f"Timestamp: {source.get('@timestamp', 'N/A')}")
            print(f"ConversationId: {source.get('conversationId', 'N/A')}")
            print(f"TurnId: {source.get('turnId', 'N/A')}")
            print(f"Event: {source.get('event', 'N/A')}")
            
            # Print all fields with their values (truncated if long)
            print("\nAll fields:")
            for key, value in sorted(source.items()):
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2)[:200] + ("..." if len(str(value)) > 200 else "")
                else:
                    value_str = str(value)[:200] + ("..." if len(str(value)) > 200 else "")
                print(f"  {key:30} = {value_str}")
        
        print(f"\n📊 All unique fields in this event type ({len(all_fields)}):")
        for field in sorted(all_fields):
            print(f"  - {field}")
        
        return hits
        
    except Exception as e:
        print(f"❌ Error exploring event: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_field_values(client, event_name, field_name, top_n=10):
    """Analyze the values in a specific field"""
    print(f"\n📊 Analyzing field '{field_name}' in event '{event_name}'")
    
    query = {
        "size": 0,
        "query": {
            "term": {"event": event_name}
        },
        "aggs": {
            "field_values": {
                "terms": {
                    "field": f"{field_name}.keyword",
                    "size": top_n
                }
            }
        }
    }
    
    try:
        response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
        buckets = response['aggregations']['field_values']['buckets']
        
        if buckets:
            print(f"Top {len(buckets)} values:")
            for bucket in buckets:
                print(f"  {bucket['key']:30} - {bucket['doc_count']:,} occurrences")
        else:
            print("No values found (field might not be a keyword or doesn't exist)")
        
        return buckets
    except Exception as e:
        print(f"❌ Error analyzing field: {e}")
        return []

def compare_events_by_turn(client, conversation_id, turn_id):
    """Compare all events for a specific turn to understand the flow"""
    print("\n" + "=" * 70)
    print(f"🔄 COMPARING ALL EVENTS FOR TURN")
    print(f"ConversationId: {conversation_id}")
    print(f"TurnId: {turn_id}")
    print("=" * 70)
    
    query = {
        "size": 100,
        "query": {
            "bool": {
                "must": [
                    {"term": {"conversationId": conversation_id}},
                    {"term": {"turnId": turn_id}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "asc"}}]
    }
    
    try:
        response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
        hits = response['hits']['hits']
        
        if not hits:
            print("No events found for this turn")
            return []
        
        print(f"\nFound {len(hits)} events for this turn:\n")
        
        for i, hit in enumerate(hits, 1):
            source = hit['_source']
            print(f"{i:3}. {source.get('@timestamp', 'N/A')[:19]} | {source.get('event', 'N/A'):40} | {source.get('step', 'N/A')}")
        
        return hits
        
    except Exception as e:
        print(f"❌ Error comparing events: {e}")
        return []

def main():
    """Main exploration function"""
    print("🚀 OpenSearch Field Explorer")
    print("=" * 70)
    
    # Calculate date range (last 4 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=4)
    
    # Connect to OpenSearch
    client = connect_to_opensearch()
    if not client:
        return
    
    # 1. Get all event types
    event_types = get_all_event_types(client)
    
    # 2. Search for events containing "variant" or "ab" or "experiment"
    print("\n" * 2)
    print("=" * 70)
    print("🔍 SEARCHING FOR AB/EXPERIMENT RELATED EVENTS")
    print("=" * 70)
    
    # Search for events with variant or ab in the name
    query = {
        "size": 0,
        "query": {
            "bool": {
                "should": [
                    {"wildcard": {"event": "*variant*"}},
                    {"wildcard": {"event": "*ab*"}},
                    {"wildcard": {"event": "*experiment*"}}
                ]
            }
        },
        "aggs": {
            "event_types": {
                "terms": {
                    "field": "event.keyword",
                    "size": 20
                }
            }
        }
    }
    
    try:
        response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
        buckets = response['aggregations']['event_types']['buckets']
        if buckets:
            print("\nFound events related to AB/experiments:")
            for bucket in buckets:
                print(f"  - {bucket['key']:50} - {bucket['doc_count']:,} events")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Explore AB_EXPERIMENT_RETRIEVED event
    print("\n" * 2)
    ab_events = explore_event_structure(client, "AB_EXPERIMENT_RETRIEVED", num_samples=5)
    
    # 4. Explore RESPONSE_GENERATION_COMPLETED event in detail
    print("\n" * 2)
    completion_events = explore_event_structure(client, "RESPONSE_GENERATION_COMPLETED", num_samples=5)
    
    # 5. Search for documents with variant fields
    print("\n" * 2)
    print("=" * 70)
    print("🔍 SEARCHING FOR DOCUMENTS WITH VARIANT FIELDS")
    print("=" * 70)
    
    variant_query = {
        "size": 5,
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "ab_experiment_variant"}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}]
    }
    
    variant_hits = []
    try:
        variant_response = client.search(index=OPENSEARCH_CONFIG['index'], body=variant_query)
        variant_hits = variant_response['hits']['hits']
        if variant_hits:
            print(f"\nFound {len(variant_hits)} documents with 'ab_experiment_variant' field:")
            for i, hit in enumerate(variant_hits, 1):
                source = hit['_source']
                print(f"\n--- Sample {i} ---")
                print(f"Event: {source.get('event', 'N/A')}")
                print(f"Variant: {source.get('ab_experiment_variant', 'N/A')}")
                print(f"ConversationId: {source.get('conversationId', 'N/A')}")
                print(f"TurnId: {source.get('turnId', 'N/A')}")
                # Show all fields that contain 'variant' or 'experiment' or 'ab'
                relevant_fields = {k: v for k, v in source.items() 
                                 if any(keyword in k.lower() for keyword in ['variant', 'experiment', 'ab'])}
                if relevant_fields:
                    print("\nRelevant fields:")
                    for k, v in relevant_fields.items():
                        print(f"  {k}: {v}")
    except Exception as e:
        print(f"Error searching for variant fields: {e}")
    
    # 6. Analyze variant field values
    if variant_hits:
        print("\n" * 2)
        # Try to analyze variant values from any event that has this field
        print("=" * 70)
        print("📊 ANALYZING VARIANT FIELD VALUES")
        print("=" * 70)
        
        variant_agg_query = {
            "size": 0,
            "query": {
                "exists": {"field": "ab_experiment_variant"}
            },
            "aggs": {
                "variants": {
                    "terms": {
                        "field": "ab_experiment_variant.keyword",
                        "size": 20
                    }
                }
            }
        }
        
        try:
            variant_agg_response = client.search(index=OPENSEARCH_CONFIG['index'], body=variant_agg_query)
            variant_buckets = variant_agg_response['aggregations']['variants']['buckets']
            if variant_buckets:
                print("\nVariant values found:")
                for bucket in variant_buckets:
                    print(f"  {bucket['key']:30} - {bucket['doc_count']:,} occurrences")
        except Exception as e:
            print(f"Error analyzing variants: {e}")
    
    # 7. Analyze status/result fields in completion events
    if completion_events:
        print("\n" * 2)
        print("=" * 70)
        print("📊 ANALYZING COMPLETION STATUS FIELDS")
        print("=" * 70)
        # Try different possible field names for status
        for field_name in ["status", "result", "completion_status", "completionStatus", "outcome", "responseStatus", "turnStatus"]:
            print(f"\nTrying field: {field_name}")
            analyze_field_values(client, "RESPONSE_GENERATION_COMPLETED", field_name, top_n=10)
    
    # 6. Find a turn that has both events and compare
    print("\n" * 2)
    print("=" * 70)
    print("🔍 FINDING TURNS WITH BOTH AB_EXPERIMENT_VARIANT AND RESPONSE_GENERATION_COMPLETED")
    print("=" * 70)
    
    # Find a turn that has both events
    query = {
        "size": 5,
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": start_date.strftime('%Y-%m-%dT00:00:00Z')}}},
                    {"term": {"event": "ab_experiment_variant"}}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}]
    }
    
    try:
        response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
        hits = response['hits']['hits']
        
        if hits:
            # Take first hit and find all events for that turn
            sample_hit = hits[0]
            conv_id = sample_hit['_source'].get('conversationId')
            turn_id = sample_hit['_source'].get('turnId')
            
            if conv_id and turn_id:
                compare_events_by_turn(client, conv_id, turn_id)
    except Exception as e:
        print(f"Error finding sample turn: {e}")
    
    # 7. Summary of key fields across all events
    print("\n" * 2)
    print("=" * 70)
    print("📋 SUMMARY: KEY FIELDS TO UNDERSTAND")
    print("=" * 70)
    
    key_events = ["ab_experiment_variant", "RESPONSE_GENERATION_COMPLETED", 
                  "CHAT_REQUEST_PROCESSING_STARTED", "RESPONSE_RETURNED"]
    
    all_important_fields = {}
    for event_name in key_events:
        query = {
            "size": 1,
            "query": {"term": {"event": event_name}}
        }
        try:
            response = client.search(index=OPENSEARCH_CONFIG['index'], body=query)
            if response['hits']['hits']:
                source = response['hits']['hits'][0]['_source']
                all_important_fields[event_name] = list(source.keys())
        except:
            pass
    
    print("\nFields present in each event type:")
    for event_name, fields in all_important_fields.items():
        print(f"\n{event_name}:")
        for field in sorted(fields):
            print(f"  - {field}")
    
    print("\n" + "=" * 70)
    print("✅ Exploration complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()

