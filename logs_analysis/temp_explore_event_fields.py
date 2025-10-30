#!/usr/bin/env python3
"""
Event-to-Field Relationship Exploration
Analyze which fields are relevant to which event types.
"""

import json
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Any
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
            verify_certs=OPENSEARCH_CONFIG['verify_certs'],
            timeout=60,
            max_retries=3
        )
        print("✅ Successfully connected to OpenSearch")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to OpenSearch: {e}")
        return None

def extract_all_fields_recursively(doc, prefix="", level=0):
    """Recursively extract all field names from a document"""
    fields = set()
    if isinstance(doc, dict):
        for key, value in doc.items():
            full_field_name = f"{prefix}.{key}" if prefix else key
            fields.add(full_field_name)
            
            if isinstance(value, dict):
                fields.update(extract_all_fields_recursively(value, full_field_name, level + 1))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                for i, item in enumerate(value[:3]):  # Limit list items
                    fields.update(extract_all_fields_recursively(item, f"{full_field_name}[{i}]", level + 1))
    
    return fields

def get_all_event_types(client):
    """Get all unique event types"""
    print("\n🔍 Discovering all event types...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    query = {
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
            body=query
        )
        
        event_types = []
        for bucket in response['aggregations']['event_types']['buckets']:
            event_types.append({
                'event': bucket['key'],
                'count': bucket['doc_count']
            })
        
        print(f"✅ Found {len(event_types)} unique event types")
        return event_types
        
    except Exception as e:
        print(f"❌ Error getting event types: {e}")
        return []

def sample_documents_for_event(client, event_type: str, sample_size: int = 50):
    """Sample documents for a specific event type"""
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    query = {
        "size": sample_size,
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
    
    try:
        response = client.search(
            index=OPENSEARCH_CONFIG['index'],
            body=query
        )
        
        return response['hits']['hits']
        
    except Exception as e:
        print(f"    ⚠️  Error sampling {event_type}: {e}")
        return []

def analyze_fields_for_event(client, event_type: str, sample_size: int = 100):
    """Analyze which fields appear in documents for a specific event type"""
    print(f"  Analyzing: {event_type}")
    
    # Sample documents
    samples = sample_documents_for_event(client, event_type, sample_size)
    
    if not samples:
        return None
    
    # Collect all fields from all samples
    all_fields = set()
    field_frequency = Counter()
    field_value_examples = defaultdict(list)
    
    for sample in samples:
        source = sample.get('_source', {})
        fields = extract_all_fields_recursively(source)
        all_fields.update(fields)
        
        # Count field frequency
        for field in fields:
            field_frequency[field] += 1
        
        # Collect sample values for each field (limit to 5 examples per field)
        for field in fields:
            if field in source or '.' in field:
                try:
                    # Navigate to the field value
                    value = source
                    for part in field.split('.'):
                        if '[' in part:
                            # Handle array access
                            field_name, index = part.split('[')
                            index = int(index.rstrip(']'))
                            value = value.get(field_name, [])
                            if isinstance(value, list) and index < len(value):
                                value = value[index]
                            else:
                                value = None
                                break
                        else:
                            value = value.get(part) if isinstance(value, dict) else None
                            if value is None:
                                break
                    
                    if value is not None and len(field_value_examples[field]) < 5:
                        value_str = str(value)
                        if len(value_str) > 200:
                            value_str = value_str[:200] + "..."
                        field_value_examples[field].append(value_str)
                except:
                    pass
    
    # Calculate field presence percentage
    total_samples = len(samples)
    field_stats = {}
    
    for field in all_fields:
        frequency = field_frequency[field]
        percentage = (frequency / total_samples) * 100
        
        field_stats[field] = {
            'frequency': frequency,
            'percentage': round(percentage, 2),
            'presence': 'common' if percentage >= 80 else ('occasional' if percentage >= 20 else 'rare'),
            'sample_values': field_value_examples.get(field, [])[:3]
        }
    
    # Get top fields (by frequency)
    top_fields = sorted(field_stats.items(), key=lambda x: x[1]['frequency'], reverse=True)
    
    return {
        'event_type': event_type,
        'total_samples': total_samples,
        'total_fields': len(all_fields),
        'field_stats': field_stats,
        'top_fields': [{'field': f, **stats} for f, stats in top_fields[:30]],
        'common_fields': [f for f, stats in field_stats.items() if stats['presence'] == 'common'],
        'occasional_fields': [f for f, stats in field_stats.items() if stats['presence'] == 'occasional'],
        'rare_fields': [f for f, stats in field_stats.items() if stats['presence'] == 'rare']
    }

def analyze_all_events(client, event_types: List[Dict], max_events: int = 50):
    """Analyze fields for all event types"""
    print(f"\n🔍 Analyzing fields for {min(len(event_types), max_events)} event types...")
    
    results = {}
    
    # Sort by count (most common events first)
    sorted_events = sorted(event_types, key=lambda x: x['count'], reverse=True)[:max_events]
    
    for i, event_info in enumerate(sorted_events, 1):
        event_type = event_info['event']
        print(f"\n[{i}/{len(sorted_events)}] Processing: {event_type} ({event_info['count']} occurrences)")
        
        try:
            analysis = analyze_fields_for_event(client, event_type, sample_size=100)
            if analysis:
                results[event_type] = analysis
        except Exception as e:
            print(f"    ❌ Error analyzing {event_type}: {e}")
    
    return results

def create_field_event_mapping(event_analyses: Dict):
    """Create reverse mapping: field -> events where it appears"""
    print("\n📊 Creating field-to-event mapping...")
    
    field_to_events = defaultdict(list)
    
    for event_type, analysis in event_analyses.items():
        for field, stats in analysis['field_stats'].items():
            field_to_events[field].append({
                'event': event_type,
                'frequency': stats['frequency'],
                'percentage': stats['percentage'],
                'presence': stats['presence']
            })
    
    # Sort events by frequency for each field
    for field in field_to_events:
        field_to_events[field].sort(key=lambda x: x['frequency'], reverse=True)
    
    print(f"✅ Mapped {len(field_to_events)} fields to events")
    
    return field_to_events

def create_summary_report(event_analyses: Dict, field_to_events: Dict):
    """Create a summary report"""
    print("\n📝 Generating summary report...")
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_events_analyzed': len(event_analyses),
        'total_unique_fields': len(field_to_events),
        'event_summary': {},
        'common_event_fields': {},
        'field_usage_patterns': {}
    }
    
    # Event summary
    for event_type, analysis in event_analyses.items():
        summary['event_summary'][event_type] = {
            'total_fields': analysis['total_fields'],
            'common_fields_count': len(analysis['common_fields']),
            'occasional_fields_count': len(analysis['occasional_fields']),
            'rare_fields_count': len(analysis['rare_fields']),
            'top_10_fields': [f['field'] for f in analysis['top_fields'][:10]]
        }
    
    # Find fields that appear in multiple events
    multi_event_fields = {f: events for f, events in field_to_events.items() if len(events) > 1}
    
    # Group by number of events
    fields_by_event_count = defaultdict(list)
    for field, events in multi_event_fields.items():
        fields_by_event_count[len(events)].append({
            'field': field,
            'events': [e['event'] for e in events[:5]],  # Top 5 events
            'total_events': len(events)
        })
    
    summary['field_usage_patterns'] = {
        'fields_in_single_event': len(field_to_events) - len(multi_event_fields),
        'fields_in_multiple_events': len(multi_event_fields),
        'fields_by_event_count': {str(k): v for k, v in fields_by_event_count.items()}
    }
    
    # Find most common fields across all events
    event_counts = Counter()
    for field, events in field_to_events.items():
        event_counts[field] = len(events)
    
    summary['common_event_fields'] = {
        'most_common_fields': [
            {'field': field, 'appears_in_events': count}
            for field, count in event_counts.most_common(20)
        ]
    }
    
    return summary

def main():
    """Main function"""
    print("🚀 Event-to-Field Relationship Exploration")
    print("=" * 70)
    
    # Connect to OpenSearch
    client = connect_to_opensearch()
    if not client:
        return
    
    # Step 1: Get all event types
    event_types = get_all_event_types(client)
    if not event_types:
        print("❌ No event types found. Exiting.")
        return
    
    print(f"\n📊 Event Type Distribution:")
    print(f"  Total event types: {len(event_types)}")
    print(f"  Top 10 most common:")
    for i, event in enumerate(event_types[:10], 1):
        print(f"    {i}. {event['event']}: {event['count']:,} occurrences")
    
    # Step 2: Analyze fields for each event type
    event_analyses = analyze_all_events(client, event_types, max_events=50)
    
    if not event_analyses:
        print("❌ No event analyses completed. Exiting.")
        return
    
    # Step 3: Create field-to-event mapping
    field_to_events = create_field_event_mapping(event_analyses)
    
    # Step 4: Create summary report
    summary = create_summary_report(event_analyses, field_to_events)
    
    # Step 5: Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'event_types_analyzed': len(event_analyses),
        'event_analyses': event_analyses,
        'field_to_events': {k: v for k, v in list(field_to_events.items())[:100]},  # Limit for size
        'summary': summary
    }
    
    # Save detailed JSON
    output_file = 'event_field_relationships.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Saved detailed results to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 EXPLORATION SUMMARY")
    print("=" * 70)
    print(f"Events analyzed: {len(event_analyses)}")
    print(f"Total unique fields: {len(field_to_events)}")
    print(f"Fields in multiple events: {summary['field_usage_patterns']['fields_in_multiple_events']}")
    print(f"Fields in single event: {summary['field_usage_patterns']['fields_in_single_event']}")
    
    print("\n🔍 Top 10 Most Common Fields Across Events:")
    for field_info in summary['common_event_fields']['most_common_fields'][:10]:
        print(f"  - {field_info['field']}: appears in {field_info['appears_in_events']} event types")
    
    print("\n🔍 Events with Most Fields:")
    sorted_events = sorted(
        summary['event_summary'].items(),
        key=lambda x: x[1]['total_fields'],
        reverse=True
    )[:10]
    
    for event_type, info in sorted_events:
        print(f"  - {event_type}: {info['total_fields']} fields ({info['common_fields_count']} common, {info['occasional_fields_count']} occasional, {info['rare_fields_count']} rare)")
    
    print("\n🔍 Example: Top Fields for Each Event Type:")
    for event_type, analysis in list(event_analyses.items())[:10]:
        print(f"\n  {event_type}:")
        for field_info in analysis['top_fields'][:5]:
            print(f"    - {field_info['field']}: {field_info['percentage']}% ({field_info['frequency']}/{analysis['total_samples']})")
    
    print("\n" + "=" * 70)
    print("✅ Event-to-field exploration complete!")
    print(f"Review {output_file} for detailed analysis")

if __name__ == "__main__":
    main()

