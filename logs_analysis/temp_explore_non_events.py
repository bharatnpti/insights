#!/usr/bin/env python3
"""
Non-Event Documents Exploration
Analyze documents that don't have an 'event' field to understand:
- What types of documents exist without events
- What fields they contain
- How to categorize and query them
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

def get_non_event_document_count(client):
    """Get count of documents without event field"""
    print("\n🔍 Counting documents without 'event' field...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"range": {
                        "@timestamp": {
                            "gte": start_date,
                            "lte": end_date
                        }
                    }},
                    {"bool": {
                        "must_not": [
                            {"exists": {"field": "event"}}
                        ]
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
        
        count = response['hits']['total']['value']
        print(f"✅ Found {count:,} documents without 'event' field")
        return count
        
    except Exception as e:
        print(f"❌ Error counting non-event documents: {e}")
        return 0

def categorize_non_event_documents(client, sample_size: int = 1000):
    """Categorize non-event documents by common patterns"""
    print("\n🔍 Categorizing non-event documents...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Sample documents
    query = {
        "size": sample_size,
        "query": {
            "bool": {
                "must": [
                    {"range": {
                        "@timestamp": {
                            "gte": start_date,
                            "lte": end_date
                        }
                    }},
                    {"bool": {
                        "must_not": [
                            {"exists": {"field": "event"}}
                        ]
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
        
        samples = response['hits']['hits']
        print(f"  ✅ Sampled {len(samples)} documents")
        
        # Categorize by common fields
        categories = {
            'by_container': defaultdict(list),
            'by_log_level': defaultdict(list),
            'by_logger': defaultdict(list),
            'by_message_pattern': defaultdict(list),
            'by_service': defaultdict(list)
        }
        
        all_fields = set()
        field_frequency = Counter()
        
        for sample in samples:
            source = sample.get('_source', {})
            
            # Extract all fields
            fields = extract_all_fields_recursively(source)
            all_fields.update(fields)
            field_frequency.update(fields)
            
            # Categorize
            container = source.get('k8s_container', 'unknown')
            categories['by_container'][container].append(sample)
            
            log_level = source.get('level', 'unknown')
            categories['by_log_level'][log_level].append(sample)
            
            logger = source.get('logger_name', 'unknown')
            categories['by_logger'][logger].append(sample)
            
            service = source.get('k8s_name', 'unknown')
            categories['by_service'][service].append(sample)
            
            # Categorize by message pattern
            message = source.get('message', '')
            if 'error' in message.lower() or 'exception' in message.lower():
                categories['by_message_pattern']['error'].append(sample)
            elif 'http' in message.lower() or 'request' in message.lower():
                categories['by_message_pattern']['http'].append(sample)
            elif 'started' in message.lower() or 'start' in message.lower():
                categories['by_message_pattern']['startup'].append(sample)
            elif 'completed' in message.lower() or 'done' in message.lower():
                categories['by_message_pattern']['completion'].append(sample)
            else:
                categories['by_message_pattern']['other'].append(sample)
        
        print(f"  ✅ Categorized into {len(categories)} dimensions")
        
        return {
            'samples': samples,
            'categories': categories,
            'all_fields': all_fields,
            'field_frequency': field_frequency
        }
        
    except Exception as e:
        print(f"❌ Error categorizing documents: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_non_event_fields(client, categories: Dict):
    """Analyze fields in non-event documents"""
    print("\n🔍 Analyzing fields in non-event documents...")
    
    if not categories:
        return None
    
    samples = categories['samples']
    
    # Analyze fields by category
    field_analysis = {
        'by_container': {},
        'by_log_level': {},
        'by_logger': {},
        'by_service': {}
    }
    
    # Analyze by container
    for container, container_samples in list(categories['categories']['by_container'].items())[:20]:
        container_fields = set()
        for sample in container_samples[:50]:  # Limit samples
            source = sample.get('_source', {})
            container_fields.update(extract_all_fields_recursively(source))
        
        field_analysis['by_container'][container] = {
            'sample_count': len(container_samples),
            'total_fields': len(container_fields),
            'common_fields': sorted(container_fields)[:30]  # Top 30
        }
    
    # Analyze by log level
    for level, level_samples in categories['categories']['by_log_level'].items():
        level_fields = set()
        for sample in level_samples[:50]:
            source = sample.get('_source', {})
            level_fields.update(extract_all_fields_recursively(source))
        
        field_analysis['by_log_level'][level] = {
            'sample_count': len(level_samples),
            'total_fields': len(level_fields),
            'common_fields': sorted(level_fields)[:30]
        }
    
    # Analyze by logger
    for logger, logger_samples in list(categories['categories']['by_logger'].items())[:20]:
        logger_fields = set()
        for sample in logger_samples[:50]:
            source = sample.get('_source', {})
            logger_fields.update(extract_all_fields_recursively(source))
        
        field_analysis['by_logger'][logger] = {
            'sample_count': len(logger_samples),
            'total_fields': len(logger_fields),
            'common_fields': sorted(logger_fields)[:30]
        }
    
    # Analyze by service
    for service, service_samples in list(categories['categories']['by_service'].items())[:20]:
        service_fields = set()
        for sample in service_samples[:50]:
            source = sample.get('_source', {})
            service_fields.update(extract_all_fields_recursively(source))
        
        field_analysis['by_service'][service] = {
            'sample_count': len(service_samples),
            'total_fields': len(service_fields),
            'common_fields': sorted(service_fields)[:30]
        }
    
    return field_analysis

def analyze_non_event_patterns(categories: Dict):
    """Analyze patterns in non-event documents"""
    print("\n🔍 Analyzing patterns in non-event documents...")
    
    if not categories:
        return None
    
    samples = categories['samples']
    
    # Analyze common field combinations
    common_fields = {
        'container_fields': Counter(),
        'level_fields': Counter(),
        'logger_fields': Counter(),
        'message_patterns': Counter()
    }
    
    # Collect field statistics
    field_stats = defaultdict(lambda: {
        'containers': set(),
        'levels': set(),
        'loggers': set(),
        'sample_values': []
    })
    
    for sample in samples:
        source = sample.get('_source', {})
        fields = extract_all_fields_recursively(source)
        
        container = source.get('k8s_container', 'unknown')
        level = source.get('level', 'unknown')
        logger = source.get('logger_name', 'unknown')
        message = source.get('message', '')
        
        # Track which fields appear with which containers/levels/loggers
        for field in fields:
            field_stats[field]['containers'].add(container)
            field_stats[field]['levels'].add(level)
            field_stats[field]['loggers'].add(logger)
            
            # Collect sample values (limit to 3)
            if len(field_stats[field]['sample_values']) < 3:
                try:
                    # Try to get field value
                    value = source
                    for part in field.split('.'):
                        if '[' in part:
                            continue  # Skip array access
                        value = value.get(part) if isinstance(value, dict) else None
                        if value is None:
                            break
                    
                    if value is not None:
                        value_str = str(value)
                        if len(value_str) > 200:
                            value_str = value_str[:200] + "..."
                        field_stats[field]['sample_values'].append(value_str)
                except:
                    pass
    
    # Convert sets to lists for JSON
    field_stats_serializable = {}
    for field, stats in field_stats.items():
        field_stats_serializable[field] = {
            'containers': list(stats['containers'])[:10],  # Top 10
            'levels': list(stats['levels']),
            'loggers': list(stats['loggers'])[:10],  # Top 10
            'sample_values': stats['sample_values']
        }
    
    return {
        'field_stats': field_stats_serializable,
        'total_fields': len(field_stats)
    }

def get_non_event_aggregations(client):
    """Get aggregations for non-event documents"""
    print("\n🔍 Getting aggregations for non-event documents...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    query = {
        "size": 0,
        "aggs": {
            "by_container": {
                "terms": {
                    "field": "k8s_container.keyword",
                    "size": 30
                }
            },
            "by_level": {
                "terms": {
                    "field": "level.keyword",
                    "size": 10
                }
            },
            "by_logger": {
                "terms": {
                    "field": "logger_name.keyword",
                    "size": 30
                }
            },
            "by_service": {
                "terms": {
                    "field": "k8s_name.keyword",
                    "size": 30
                }
            },
            "by_message_keywords": {
                "terms": {
                    "field": "message.keyword",
                    "size": 20
                }
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"range": {
                        "@timestamp": {
                            "gte": start_date,
                            "lte": end_date
                        }
                    }},
                    {"bool": {
                        "must_not": [
                            {"exists": {"field": "event"}}
                        ]
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
        
        aggregations = {
            'by_container': {},
            'by_level': {},
            'by_logger': {},
            'by_service': {},
            'by_message_keywords': {}
        }
        
        # By container
        for bucket in response['aggregations']['by_container']['buckets']:
            aggregations['by_container'][bucket['key']] = bucket['doc_count']
        
        # By level
        for bucket in response['aggregations']['by_level']['buckets']:
            aggregations['by_level'][bucket['key']] = bucket['doc_count']
        
        # By logger
        for bucket in response['aggregations']['by_logger']['buckets']:
            aggregations['by_logger'][bucket['key']] = bucket['doc_count']
        
        # By service
        for bucket in response['aggregations']['by_service']['buckets']:
            aggregations['by_service'][bucket['key']] = bucket['doc_count']
        
        # By message keywords
        for bucket in response['aggregations']['by_message_keywords']['buckets']:
            aggregations['by_message_keywords'][bucket['key']] = bucket['doc_count']
        
        print(f"  ✅ Aggregated by {len(aggregations)} dimensions")
        
        return aggregations
        
    except Exception as e:
        print(f"❌ Error getting aggregations: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    """Main function"""
    print("🚀 Non-Event Documents Exploration")
    print("=" * 70)
    
    # Connect to OpenSearch
    client = connect_to_opensearch()
    if not client:
        return
    
    # Step 1: Count non-event documents
    total_count = get_non_event_document_count(client)
    
    if total_count == 0:
        print("❌ No non-event documents found. Exiting.")
        return
    
    # Step 2: Get aggregations
    aggregations = get_non_event_aggregations(client)
    
    # Step 3: Categorize documents
    categories = categorize_non_event_documents(client, sample_size=1000)
    
    if not categories:
        print("❌ Failed to categorize documents. Exiting.")
        return
    
    # Step 4: Analyze fields
    field_analysis = analyze_non_event_fields(client, categories)
    
    # Step 5: Analyze patterns
    pattern_analysis = analyze_non_event_patterns(categories)
    
    # Step 6: Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_non_event_documents': total_count,
        'aggregations': aggregations,
        'categories_summary': {
            'by_container': {k: len(v) for k, v in categories['categories']['by_container'].items()},
            'by_log_level': {k: len(v) for k, v in categories['categories']['by_log_level'].items()},
            'by_logger': {k: len(v) for k, v in list(categories['categories']['by_logger'].items())[:30]},
            'by_service': {k: len(v) for k, v in categories['categories']['by_service'].items()},
            'by_message_pattern': {k: len(v) for k, v in categories['categories']['by_message_pattern'].items()}
        },
        'field_analysis': field_analysis,
        'pattern_analysis': pattern_analysis,
        'top_fields': dict(categories['field_frequency'].most_common(50))
    }
    
    # Save detailed JSON
    output_file = 'non_event_documents_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Saved detailed results to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 EXPLORATION SUMMARY")
    print("=" * 70)
    print(f"Total non-event documents: {total_count:,}")
    print(f"Total unique fields found: {len(categories['all_fields'])}")
    
    print("\n🔍 Top Containers (by document count):")
    sorted_containers = sorted(
        aggregations['by_container'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    for container, count in sorted_containers:
        print(f"  - {container}: {count:,} documents")
    
    print("\n🔍 Top Log Levels:")
    sorted_levels = sorted(
        aggregations['by_level'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    for level, count in sorted_levels:
        print(f"  - {level}: {count:,} documents")
    
    print("\n🔍 Top Services:")
    sorted_services = sorted(
        aggregations['by_service'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    for service, count in sorted_services:
        print(f"  - {service}: {count:,} documents")
    
    print("\n🔍 Top Loggers:")
    sorted_loggers = sorted(
        aggregations['by_logger'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    for logger, count in sorted_loggers:
        print(f"  - {logger}: {count:,} documents")
    
    print("\n🔍 Top Fields in Non-Event Documents:")
    for field, count in categories['field_frequency'].most_common(20):
        print(f"  - {field}: appears in {count} documents")
    
    print("\n🔍 Message Patterns:")
    for pattern, samples in categories['categories']['by_message_pattern'].items():
        print(f"  - {pattern}: {len(samples)} documents")
    
    print("\n" + "=" * 70)
    print("✅ Non-event documents exploration complete!")
    print(f"Review {output_file} for detailed analysis")

if __name__ == "__main__":
    main()

