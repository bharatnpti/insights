#!/usr/bin/env python3
"""
Broad Log Exploration - Extended Analysis
Explore OpenSearch logs more comprehensively to understand:
- Field relationships and co-occurrences
- Nested field structures
- Event sequences and flows
- Performance metrics
- Error patterns
- Service interactions
- User interaction patterns
"""

import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set, Tuple
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
            timeout=60,  # Increase timeout
            max_retries=3
        )
        print("✅ Successfully connected to OpenSearch")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to OpenSearch: {e}")
        return None

def explore_field_co_occurrences(client):
    """Explore which fields appear together in documents"""
    print("\n🔍 Exploring field co-occurrences...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Key fields to check co-occurrence
    key_fields = [
        "ab_experiment_variant",
        "response_status",
        "conversationId",
        "turnId",
        "event",
        "markedForAgentHandover",
        "markedResolved"
    ]
    
    co_occurrence_matrix = {}
    
    for i, field1 in enumerate(key_fields):
        for field2 in key_fields[i+1:]:
            print(f"  Checking: {field1} + {field2}")
            
            # Query for documents with both fields
            query = {
                "size": 0,
                "query": {
                    "bool": {
                        "must": [
                            {"exists": {"field": field1}},
                            {"exists": {"field": field2}},
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
                
                count = response['hits']['total']['value']
                co_occurrence_matrix[f"{field1} + {field2}"] = count
                print(f"    ✅ {count} documents have both fields")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    return co_occurrence_matrix

def explore_nested_structures(client):
    """Explore nested object and array structures"""
    print("\n🔍 Exploring nested structures...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Sample various event types to find nested structures
    query = {
        "size": 50,
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
    }
    
    try:
        response = client.search(
            index=OPENSEARCH_CONFIG['index'],
            body=query
        )
        
        nested_structures = []
        
        for hit in response['hits']['hits']:
            source = hit['_source']
            event_type = source.get('event', 'unknown')
            
            # Recursively find nested structures
            def find_nested(obj, path="", depth=0):
                if depth > 3:  # Limit depth
                    return
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        if isinstance(value, dict):
                            nested_structures.append({
                                'path': current_path,
                                'type': 'object',
                                'event_type': event_type,
                                'depth': depth
                            })
                            find_nested(value, current_path, depth + 1)
                        elif isinstance(value, list) and value and isinstance(value[0], dict):
                            nested_structures.append({
                                'path': current_path,
                                'type': 'array[object]',
                                'event_type': event_type,
                                'depth': depth,
                                'sample_length': len(value)
                            })
                            if value:
                                find_nested(value[0], f"{current_path}[0]", depth + 1)
                
            find_nested(source)
        
        # Deduplicate
        unique_nested = {}
        for ns in nested_structures:
            key = ns['path']
            if key not in unique_nested:
                unique_nested[key] = ns
        
        print(f"✅ Found {len(unique_nested)} unique nested structures")
        return list(unique_nested.values())
        
    except Exception as e:
        print(f"❌ Error exploring nested structures: {e}")
        return []

def explore_event_sequences(client):
    """Explore typical event sequences in conversations"""
    print("\n🔍 Exploring event sequences...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Simplified approach: Get sample conversations with their events
    query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "conversationId"}},
                    {"exists": {"field": "event"}},
                    {"range": {
                        "@timestamp": {
                            "gte": start_date,
                            "lte": end_date
                        }
                    }}
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "asc"}}]
    }
    
    try:
        # Get sample conversations
        response = client.search(
            index=OPENSEARCH_CONFIG['index'],
            body=query
        )
        
        # Group by conversation
        conversations = {}
        for hit in response['hits']['hits']:
            conv_id = hit['_source'].get('conversationId')
            if conv_id:
                if conv_id not in conversations:
                    conversations[conv_id] = []
                conversations[conv_id].append({
                    'event': hit['_source'].get('event'),
                    'timestamp': hit['_source'].get('@timestamp'),
                    'turnId': hit['_source'].get('turnId')
                })
        
        # Get more events for each conversation (simplified)
        sequences = []
        for conv_id, events in list(conversations.items())[:10]:
            # Get more events for this conversation
            conv_query = {
                "size": 20,
                "query": {
                    "bool": {
                        "should": [
                            {"term": {"conversationId": conv_id}},
                            {"term": {"conversation_id": conv_id}}
                        ],
                        "must": [
                            {"range": {
                                "@timestamp": {
                                    "gte": start_date,
                                    "lte": end_date
                                }
                            }}
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "asc"}}]
            }
            
            try:
                conv_response = client.search(
                    index=OPENSEARCH_CONFIG['index'],
                    body=conv_query
                )
                
                conv_events = []
                for hit in conv_response['hits']['hits']:
                    conv_events.append({
                        'event': hit['_source'].get('event'),
                        'timestamp': hit['_source'].get('@timestamp'),
                        'turnId': hit['_source'].get('turnId')
                    })
                
                sequences.append({
                    'conversationId': conv_id,
                    'event_sequence': [e['event'] for e in conv_events if e.get('event')],
                    'unique_events': list(set([e['event'] for e in conv_events if e.get('event')])),
                    'turn_count': len(set([e['turnId'] for e in conv_events if e.get('turnId')]))
                })
                
            except Exception as e2:
                print(f"    ⚠️  Error getting events for conversation {conv_id}: {e2}")
        
        print(f"✅ Analyzed {len(sequences)} conversation sequences")
        return sequences
        
    except Exception as e:
        print(f"❌ Error exploring sequences: {e}")
        return []

def explore_performance_metrics(client):
    """Explore performance-related fields"""
    print("\n🔍 Exploring performance metrics...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    performance_fields = [
        "responseTime",
        "responseTimeInMs",
        "duration",
        "upstream_service_time",
        "totalTokens",
        "completionTokens",
        "promptTokens"
    ]
    
    metrics_analysis = {}
    
    for field in performance_fields:
        print(f"  Analyzing: {field}")
        
        # Try to get statistics
        query = {
            "size": 0,
            "aggs": {
                "stats": {
                    "stats": {"field": field}
                },
                "percentiles": {
                    "percentiles": {
                        "field": field,
                        "percents": [50, 75, 90, 95, 99]
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
        
        try:
            response = client.search(
                index=OPENSEARCH_CONFIG['index'],
                body=query
            )
            
            stats = response['aggregations']['stats']
            percentiles = response['aggregations']['percentiles']['values']
            
            metrics_analysis[field] = {
                'count': stats.get('count', 0),
                'min': stats.get('min'),
                'max': stats.get('max'),
                'avg': stats.get('avg'),
                'p50': percentiles.get('50.0'),
                'p75': percentiles.get('75.0'),
                'p90': percentiles.get('90.0'),
                'p95': percentiles.get('95.0'),
                'p99': percentiles.get('99.0')
            }
            
            print(f"    ✅ Found {stats.get('count', 0)} values")
            if stats.get('avg'):
                print(f"    Average: {stats.get('avg'):.2f}")
            
        except Exception as e:
            # Field might be string type, try value analysis
            try:
                query = {
                    "size": 0,
                    "aggs": {
                        "values": {
                            "terms": {
                                "field": f"{field}.keyword",
                                "size": 20
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
                    body=query
                )
                
                buckets = response['aggregations']['values']['buckets']
                metrics_analysis[field] = {
                    'type': 'string',
                    'unique_values': len(buckets),
                    'top_values': [(b['key'], b['doc_count']) for b in buckets[:5]]
                }
                
                print(f"    ✅ Found {len(buckets)} unique string values")
                
            except Exception as e2:
                print(f"    ❌ Error: {e2}")
                metrics_analysis[field] = {'error': str(e2)}
    
    return metrics_analysis

def explore_error_patterns(client):
    """Explore error and exception patterns"""
    print("\n🔍 Exploring error patterns...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Look for error-related fields
    error_keywords = ['error', 'exception', 'fail', 'failed', 'timeout', 'error_message']
    
    error_fields = {}
    
    # First, find fields with error-related names
    query = {
        "size": 100,
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
    }
    
    try:
        response = client.search(
            index=OPENSEARCH_CONFIG['index'],
            body=query
        )
        
        # Check for error fields in sample documents
        for hit in response['hits']['hits']:
            source = hit['_source']
            for key in source.keys():
                key_lower = key.lower()
                if any(keyword in key_lower for keyword in error_keywords):
                    if key not in error_fields:
                        error_fields[key] = {
                            'sample_values': [],
                            'event_types': set()
                        }
                    
                    value = source.get(key)
                    if value and str(value) not in error_fields[key]['sample_values']:
                        error_fields[key]['sample_values'].append(str(value)[:200])
                    
                    event_type = source.get('event', 'unknown')
                    error_fields[key]['event_types'].add(event_type)
        
        # Convert sets to lists for JSON
        for field, data in error_fields.items():
            data['event_types'] = list(data['event_types'])
            data['sample_values'] = data['sample_values'][:10]  # Keep top 10
        
        print(f"✅ Found {len(error_fields)} error-related fields")
        return error_fields
        
    except Exception as e:
        print(f"❌ Error exploring error patterns: {e}")
        return {}

def explore_service_interactions(client):
    """Explore interactions between different services"""
    print("\n🔍 Exploring service interactions...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Analyze service fields
    query = {
        "size": 0,
        "aggs": {
            "services": {
                "terms": {
                    "field": "k8s_name.keyword",
                    "size": 30
                },
                "aggs": {
                    "events": {
                        "terms": {
                            "field": "event.keyword",
                            "size": 10
                        }
                    },
                    "containers": {
                        "terms": {
                            "field": "k8s_container.keyword",
                            "size": 5
                        }
                    }
                }
            }
        },
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        }
    }
    
    try:
        response = client.search(
            index=OPENSEARCH_CONFIG['index'],
            body=query
        )
        
        service_analysis = {}
        for bucket in response['aggregations']['services']['buckets']:
            service = bucket['key']
            count = bucket['doc_count']
            
            events = [b['key'] for b in bucket['events']['buckets']]
            containers = [b['key'] for b in bucket['containers']['buckets']]
            
            service_analysis[service] = {
                'total_events': count,
                'event_types': events,
                'containers': containers
            }
        
        print(f"✅ Analyzed {len(service_analysis)} services")
        return service_analysis
        
    except Exception as e:
        print(f"❌ Error exploring services: {e}")
        return {}

def explore_user_interaction_patterns(client):
    """Explore user interaction patterns"""
    print("\n🔍 Exploring user interaction patterns...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Look for user-related fields and patterns
    user_fields = [
        "channelId",
        "source_intent",
        "detectedIntent",
        "languageModel",
        "tenant"
    ]
    
    interaction_patterns = {}
    
    for field in user_fields:
        print(f"  Analyzing: {field}")
        
        query = {
            "size": 0,
            "aggs": {
                "values": {
                    "terms": {
                        "field": f"{field}.keyword",
                        "size": 20
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
        
        try:
            response = client.search(
                index=OPENSEARCH_CONFIG['index'],
                body=query
            )
            
            buckets = response['aggregations']['values']['buckets']
            interaction_patterns[field] = {
                'unique_values': len(buckets),
                'top_values': [(b['key'], b['doc_count']) for b in buckets[:10]]
            }
            
            print(f"    ✅ {len(buckets)} unique values")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return interaction_patterns

def explore_agent_patterns(client):
    """Explore agent-related patterns"""
    print("\n🔍 Exploring agent patterns...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Analyze agent selection and usage
    query = {
        "size": 0,
        "aggs": {
            "agents": {
                "terms": {
                    "field": "agent.keyword",
                    "size": 30
                },
                "aggs": {
                    "steps": {
                        "terms": {
                            "field": "step.keyword",
                            "size": 10
                        }
                    },
                    "intents": {
                        "terms": {
                            "field": "source_intent.keyword",
                            "size": 10
                        }
                    }
                }
            },
            "classifier_agents": {
                "terms": {
                    "field": "classifier-selected-agent.keyword",
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
                        "should": [
                            {"exists": {"field": "agent"}},
                            {"exists": {"field": "classifier-selected-agent"}}
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
        
        agent_analysis = {
            'agents': {},
            'classifier_agents': []
        }
        
        # Regular agents
        for bucket in response['aggregations']['agents']['buckets']:
            agent = bucket['key']
            agent_analysis['agents'][agent] = {
                'count': bucket['doc_count'],
                'top_steps': [b['key'] for b in bucket['steps']['buckets']],
                'top_intents': [b['key'] for b in bucket['intents']['buckets']]
            }
        
        # Classifier-selected agents
        for bucket in response['aggregations']['classifier_agents']['buckets']:
            agent_analysis['classifier_agents'].append({
                'agent': bucket['key'],
                'count': bucket['doc_count']
            })
        
        print(f"✅ Found {len(agent_analysis['agents'])} agents")
        print(f"✅ Found {len(agent_analysis['classifier_agents'])} classifier-selected agents")
        
        return agent_analysis
        
    except Exception as e:
        print(f"❌ Error exploring agents: {e}")
        import traceback
        traceback.print_exc()
        return {}

def explore_function_call_patterns(client):
    """Explore function call patterns"""
    print("\n🔍 Exploring function call patterns...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    # Analyze function calls
    query = {
        "size": 0,
        "aggs": {
            "functions": {
                "terms": {
                    "field": "function.keyword",
                    "size": 30
                },
                "aggs": {
                    "status": {
                        "terms": {
                            "field": "function_status.keyword",
                            "size": 10
                        }
                    },
                    "phase": {
                        "terms": {
                            "field": "phase.keyword",
                            "size": 5
                        }
                    }
                }
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "function"}},
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
        
        function_analysis = {}
        for bucket in response['aggregations']['functions']['buckets']:
            func_name = bucket['key']
            function_analysis[func_name] = {
                'count': bucket['doc_count'],
                'statuses': {b['key']: b['doc_count'] for b in bucket['status']['buckets']},
                'phases': [b['key'] for b in bucket['phase']['buckets']]
            }
        
        print(f"✅ Analyzed {len(function_analysis)} functions")
        return function_analysis
        
    except Exception as e:
        print(f"❌ Error exploring functions: {e}")
        return {}

def explore_intent_patterns(client):
    """Explore intent detection and classification patterns"""
    print("\n🔍 Exploring intent patterns...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    intent_fields = [
        "source_intent",
        "detectedIntent",
        "explicitIntent",
        "category",
        "subCategory"
    ]
    
    intent_analysis = {}
    
    for field in intent_fields:
        print(f"  Analyzing: {field}")
        
        query = {
            "size": 0,
            "aggs": {
                "values": {
                    "terms": {
                        "field": f"{field}.keyword",
                        "size": 30
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
        
        try:
            response = client.search(
                index=OPENSEARCH_CONFIG['index'],
                body=query
            )
            
            buckets = response['aggregations']['values']['buckets']
            intent_analysis[field] = {
                'unique_values': len(buckets),
                'top_values': [(b['key'], b['doc_count']) for b in buckets[:15]]
            }
            
            print(f"    ✅ {len(buckets)} unique values")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return intent_analysis

def explore_llm_usage_patterns(client):
    """Explore LLM usage patterns"""
    print("\n🔍 Exploring LLM usage patterns...")
    
    start_date = "2025-10-27T00:00:00"
    end_date = "2025-10-30T23:59:59"
    
    query = {
        "size": 0,
        "aggs": {
            "models": {
                "terms": {
                    "field": "languageModel.keyword",
                    "size": 20
                },
                "aggs": {
                    "token_stats": {
                        "stats": {"field": "totalTokens"}
                    },
                    "response_time": {
                        "stats": {"field": "responseTime"}
                    }
                }
            },
            "steps": {
                "terms": {
                    "field": "step.keyword",
                    "size": 20
                },
                "aggs": {
                    "models": {
                        "terms": {
                            "field": "languageModel.keyword",
                            "size": 5
                        }
                    }
                }
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"exists": {"field": "languageModel"}},
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
        
        llm_analysis = {
            'models': {},
            'steps': {}
        }
        
        # Model analysis
        for bucket in response['aggregations']['models']['buckets']:
            model = bucket['key']
            token_stats = bucket['token_stats']
            response_time = bucket['response_time']
            
            llm_analysis['models'][model] = {
                'count': bucket['doc_count'],
                'avg_tokens': token_stats.get('avg'),
                'total_tokens': token_stats.get('sum'),
                'avg_response_time': response_time.get('avg')
            }
        
        # Step analysis
        for bucket in response['aggregations']['steps']['buckets']:
            step = bucket['key']
            llm_analysis['steps'][step] = {
                'count': bucket['doc_count'],
                'models': {b['key']: b['doc_count'] for b in bucket['models']['buckets']}
            }
        
        print(f"✅ Analyzed {len(llm_analysis['models'])} LLM models")
        print(f"✅ Analyzed {len(llm_analysis['steps'])} steps")
        
        return llm_analysis
        
    except Exception as e:
        print(f"❌ Error exploring LLM patterns: {e}")
        return {}

def main():
    """Main function for broad exploration"""
    print("🚀 Broad Log Exploration - Extended Analysis")
    print("=" * 70)
    
    # Connect to OpenSearch
    client = connect_to_opensearch()
    if not client:
        return
    
    # Run all exploration analyses
    results = {
        'timestamp': datetime.now().isoformat(),
        'co_occurrences': {},
        'nested_structures': [],
        'event_sequences': [],
        'performance_metrics': {},
        'error_patterns': {},
        'service_interactions': {},
        'user_interactions': {},
        'agent_patterns': {},
        'function_patterns': {},
        'intent_patterns': {},
        'llm_patterns': {}
    }
    
    # Field co-occurrences
    results['co_occurrences'] = explore_field_co_occurrences(client)
    
    # Nested structures
    results['nested_structures'] = explore_nested_structures(client)
    
    # Event sequences
    results['event_sequences'] = explore_event_sequences(client)
    
    # Performance metrics
    results['performance_metrics'] = explore_performance_metrics(client)
    
    # Error patterns
    results['error_patterns'] = explore_error_patterns(client)
    
    # Service interactions
    results['service_interactions'] = explore_service_interactions(client)
    
    # User interactions
    results['user_interactions'] = explore_user_interaction_patterns(client)
    
    # Agent patterns
    results['agent_patterns'] = explore_agent_patterns(client)
    
    # Function patterns
    results['function_patterns'] = explore_function_call_patterns(client)
    
    # Intent patterns
    results['intent_patterns'] = explore_intent_patterns(client)
    
    # LLM patterns
    results['llm_patterns'] = explore_llm_usage_patterns(client)
    
    # Save comprehensive results
    output_file = 'broad_exploration_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Saved comprehensive exploration results to {output_file}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 EXPLORATION SUMMARY")
    print("=" * 70)
    print(f"Field co-occurrences: {len(results['co_occurrences'])} pairs analyzed")
    print(f"Nested structures: {len(results['nested_structures'])} found")
    print(f"Event sequences: {len(results['event_sequences'])} conversations analyzed")
    print(f"Performance metrics: {len(results['performance_metrics'])} fields analyzed")
    print(f"Error fields: {len(results['error_patterns'])} found")
    print(f"Services: {len(results['service_interactions'])} analyzed")
    print(f"User interaction fields: {len(results['user_interactions'])} analyzed")
    print(f"Agents: {len(results['agent_patterns'].get('agents', {}))} found")
    print(f"Functions: {len(results['function_patterns'])} analyzed")
    print(f"Intent fields: {len(results['intent_patterns'])} analyzed")
    print(f"LLM models: {len(results['llm_patterns'].get('models', {}))} found")
    
    print("\n🔍 Key Co-occurrences:")
    for pair, count in sorted(results['co_occurrences'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {pair}: {count} documents")
    
    print("\n🔍 Top Services by Event Count:")
    for service, data in sorted(
        results['service_interactions'].items(), 
        key=lambda x: x[1].get('total_events', 0), 
        reverse=True
    )[:10]:
        print(f"  - {service}: {data.get('total_events', 0)} events")
        print(f"    Event types: {len(data.get('event_types', []))}")
    
    print("\n" + "=" * 70)
    print("✅ Broad exploration complete!")
    print(f"Review {output_file} for detailed analysis")

if __name__ == "__main__":
    main()
