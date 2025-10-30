# Event-to-Field Relationships Documentation

**Generated:** 2025-10-31  
**Index:** `ia-platform-prod-*`  
**Date Range:** 2025-10-27 to 2025-10-30  
**Analysis Type:** Event-to-Field Relationship Mapping

---

## Executive Summary

This document provides a comprehensive mapping of which fields are relevant to which event types in the OpenSearch logs. This mapping is critical for:

- Building accurate queries for specific event types
- Understanding what data is available in each event
- Correlating events based on common fields
- Identifying event-specific fields vs. universal fields

**Key Statistics:**
- **44 event types** analyzed
- **153 unique fields** discovered
- **71 fields** appear in multiple events (shared fields)
- **82 fields** are event-specific (appear in single event only)

---

## Universal Fields (Appear in All Events)

The following fields appear in **all 44 event types** (100% presence):

| Field | Description | Usage |
|-------|-------------|-------|
| `time` | Event timestamp | Temporal tracking |
| `conversationId` | Conversation identifier | Conversation correlation |
| `k8s_version` | Kubernetes version | Infrastructure tracking |
| `message` | Log message | Debugging/observability |
| `channelId` | Communication channel | Channel identification |
| `@timestamp` | OpenSearch timestamp | Default temporal field |
| `cicd` | CI/CD service name | Deployment tracking |
| `k8s_name` | Kubernetes service name | Service identification |
| `k8s_image` | Container image | Container tracking |
| `k8s_container` | Container name | Container identification |
| `k8s_host` | Host machine | Infrastructure tracking |
| `k8s_pod` | Pod name | Pod identification |
| `k8s_namespace` | Kubernetes namespace | Namespace tracking |
| `traceId` | Distributed trace ID | Tracing correlation |
| `spanId` | Span identifier | Span tracking |
| `correlationId` | Correlation identifier | Request correlation |
| `tenantId` | Tenant identifier | Multi-tenancy |
| `tenant` | Tenant name | Multi-tenancy |
| `environment` | Environment name | Environment tracking |
| `application_id` | Application ID | Application tracking |
| `logger_name` | Logger name | Logging source |
| `thread_name` | Thread name | Thread tracking |
| `level` | Log level | Log severity |

**Usage Pattern:** These fields can be used for filtering, grouping, and correlation across all event types.

---

## Event-Specific Field Analysis

### LLM_COMPLETED (620,939 occurrences)

**Total Fields:** 57  
**Common Fields:** 37  
**Occasional Fields:** 18  
**Rare Fields:** 2

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`, `message`
- `languageModel` - LLM model used
- `promptTokens` - Tokens in prompt
- `completionTokens` - Tokens in completion
- `totalTokens` - Total tokens used
- `responseTime` - Response time
- `responseTimeInMs` - Response time in milliseconds
- `input` - Input to LLM
- `prompt` - Full prompt sent to LLM
- `result` - LLM result/response
- `agent` - Agent using LLM
- `step` - Processing step
- `seed` - Random seed used
- `authTechnicalError` - Authentication error
- `isAppDeeplinksEnabled` - Feature flag
- `variant` - A/B test variant

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "LLM_COMPLETED"}},
        {"exists": {"field": "languageModel"}},
        {"exists": {"field": "totalTokens"}}
      ]
    }
  }
}
```

### MEMORY_STORE_EVENT (288,367 occurrences)

**Total Fields:** 43  
**Common Fields:** 42  
**Occasional Fields:** 1  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `activeFeatures` - Active feature flags
- `key` - Memory key
- `value` - Memory value
- `agent` - Agent storing memory
- `callingAgent` - Agent that triggered memory store
- `sourceChannelId` - Source channel

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "MEMORY_STORE_EVENT"}},
        {"exists": {"field": "key"}},
        {"exists": {"field": "value"}}
      ]
    }
  }
}
```

### LLM_STARTED (265,571 occurrences)

**Total Fields:** 46  
**Common Fields:** 38  
**Occasional Fields:** 8  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model to use
- `agent` - Agent starting LLM
- `step` - Processing step

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "LLM_STARTED"}},
        {"exists": {"field": "languageModel"}}
      ]
    }
  }
}
```

### CHAT_REQUEST_PROCESSING_STARTED (219,443 occurrences)

**Total Fields:** 45  
**Common Fields:** 38  
**Occasional Fields:** 7  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `conversation` - Full conversation context
- `question` - User question
- `featureId` - Feature identifier
- `referrerId` - Referrer identifier
- `source_intent` - Source intent
- `natco_code` - National code

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "CHAT_REQUEST_PROCESSING_STARTED"}},
        {"exists": {"field": "conversation"}},
        {"exists": {"field": "question"}}
      ]
    }
  }
}
```

### RESPONSE_RETURNED (212,230 occurrences)

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`, `message`
- `response_status` - Completion status (ONGOING, RESOLVED, etc.)
- `languageModel` - LLM model used
- `agent` - Agent returning response
- `source_intent` - Source intent

**Critical Field:** `response_status` is the **primary completion indicator**

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "RESPONSE_RETURNED"}},
        {"exists": {"field": "response_status"}}
      ]
    }
  }
}
```

### RECEIVED_CHAT_MESSAGE (210,447 occurrences)

**Total Fields:** 40  
**Common Fields:** 38  
**Occasional Fields:** 2  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`, `environment`
- `customerFeedbackId` - Customer feedback ID
- `x-correlation-id` - Correlation ID header

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "RECEIVED_CHAT_MESSAGE"}},
        {"exists": {"field": "customerFeedbackId"}}
      ]
    }
  }
}
```

### RESPONSE_GENERATION_COMPLETED (205,866 occurrences)

**Total Fields:** 40  
**Common Fields:** 38  
**Occasional Fields:** 2  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model used

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "RESPONSE_GENERATION_COMPLETED"}},
        {"exists": {"field": "languageModel"}}
      ]
    }
  }
}
```

### TRANSCRIPT_PREPARED (175,358 occurrences)

**Total Fields:** 41  
**Common Fields:** 38  
**Occasional Fields:** 3  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `transcript` - Prepared transcript
- `log_entry_timestamp` - Log entry timestamp
- `log_entry_id` - Log entry ID

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "TRANSCRIPT_PREPARED"}},
        {"exists": {"field": "transcript"}}
      ]
    }
  }
}
```

### USECASE_PROMPT_IDENTIFIED (142,990 occurrences)

**Total Fields:** 44  
**Common Fields:** 44  
**Occasional Fields:** 0  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `activeFeatures` - Active features
- `agent` - Agent
- `callingAgent` - Calling agent
- `usecase_version` - Use case version
- `usecase_name` - Use case name
- `usecase_description` - Use case description
- `variant` - A/B test variant

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "USECASE_PROMPT_IDENTIFIED"}},
        {"exists": {"field": "usecase_name"}}
      ]
    }
  }
}
```

### FUNCTION_CALLED (97,090 occurrences)

**Total Fields:** 52  
**Common Fields:** 42  
**Occasional Fields:** 1  
**Rare Fields:** 9

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`, `message`
- `function` - Function name being called
- `phase` - Function execution phase
- `input` - Function input
- `callingAgent` - Agent calling function
- `variant` - A/B test variant
- `beta` - Beta flag

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "FUNCTION_CALLED"}},
        {"exists": {"field": "function"}},
        {"exists": {"field": "phase"}}
      ]
    }
  }
}
```

### FUNCTION_CALL_COMPLETED (97,085 occurrences)

**Total Fields:** 58  
**Common Fields:** 48  
**Occasional Fields:** 1  
**Rare Fields:** 9

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `function` - Function name
- `function_status` - Function execution status (SUCCESS/FAILED)
- `function_input` - Function input
- `function_output` - Function output
- `function_error_message` - Error message (if failed)
- `input` - Input data
- `agent` - Agent
- `callingAgent` - Calling agent
- `step` - Processing step

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "FUNCTION_CALL_COMPLETED"}},
        {"exists": {"field": "function"}},
        {"exists": {"field": "function_status"}}
      ]
    }
  }
}
```

### USER_PROFILE_UPDATED (87,354 occurrences)

**Total Fields:** 42  
**Common Fields:** 38  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `user_profile` - Updated user profile
- `source_intent` - Source intent

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "USER_PROFILE_UPDATED"}},
        {"exists": {"field": "user_profile"}}
      ]
    }
  }
}
```

### INTENT_DETECTION_COMPLETED (76,540 occurrences)

**Total Fields:** 42  
**Common Fields:** 38  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `intent_json` - Detected intent as JSON
- `category` - Intent category
- `subCategory` - Intent subcategory

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "INTENT_DETECTION_COMPLETED"}},
        {"exists": {"field": "intent_json"}}
      ]
    }
  }
}
```

### BLACKLIST_CHECKED (47,344 occurrences)

**Total Fields:** 40  
**Common Fields:** 38  
**Occasional Fields:** 2  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `agent` - Agent checking blacklist

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "BLACKLIST_CHECKED"}}
      ]
    }
  }
}
```

### INTENT_TRAFFIC_SPLIT (45,646 occurrences)

**Total Fields:** 41  
**Common Fields:** 38  
**Occasional Fields:** 3  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `detectedIntent` - Detected intent
- `explicitIntent` - Explicit intent

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "INTENT_TRAFFIC_SPLIT"}},
        {"exists": {"field": "detectedIntent"}}
      ]
    }
  }
}
```

### CLASSIFICATION_VECTOR_DONE (43,898 occurrences)

**Total Fields:** 43  
**Common Fields:** 39  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `classifier-selected-agent` - Selected agent
- `classifier-embedding-search-query` - Search query
- `classifier-embedding-search-result` - Search results
- `classifier-user-message` - User message
- `classifier-type` - Classifier type

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "CLASSIFICATION_VECTOR_DONE"}},
        {"exists": {"field": "classifier-selected-agent"}}
      ]
    }
  }
}
```

### CLASSIFICATION_VECTOR_METRICS (43,898 occurrences)

**Total Fields:** 43  
**Common Fields:** 39  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `classifier-embedding-ranking-evaluation` - Evaluation metrics
- `classifier-embedding-ranking-top-agent` - Top agent
- `classifier-embedding-ranking-thresholds` - Thresholds
- `classifier-embedding-ranking-thresholds-matched` - Threshold match status

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "CLASSIFICATION_VECTOR_METRICS"}},
        {"exists": {"field": "classifier-embedding-ranking-evaluation"}}
      ]
    }
  }
}
```

### AGENT_HANDOVER_DETECTION_COMPLETED (43,886 occurrences)

**Total Fields:** 42  
**Common Fields:** 38  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `markedForAgentHandover` - Handover flag (boolean)
- `log_entry_timestamp` - Log entry timestamp
- `log_entry_id` - Log entry ID

**Critical Field:** `markedForAgentHandover` indicates handover decision

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "AGENT_HANDOVER_DETECTION_COMPLETED"}},
        {"term": {"markedForAgentHandover": true}}
      ]
    }
  }
}
```

### CLASSIFICATION_FASTTRACK_DONE (43,840 occurrences)

**Total Fields:** 42  
**Common Fields:** 38  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `classifier-selected-agent` - Selected agent
- `classifier-is-fasttrack` - Fasttrack flag
- `classifier-type` - Classifier type

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "CLASSIFICATION_FASTTRACK_DONE"}},
        {"term": {"classifier-is-fasttrack": true}}
      ]
    }
  }
}
```

### CLASSIFICATION_LLM_DONE (43,522 occurrences)

**Total Fields:** 43  
**Common Fields:** 39  
**Occasional Fields:** 4  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model
- `classifier-selected-agent` - Selected agent
- `classifier-user-message` - User message
- `classifier-candidate-agents` - Candidate agents
- `classifier-type` - Classifier type

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "CLASSIFICATION_LLM_DONE"}},
        {"exists": {"field": "classifier-selected-agent"}}
      ]
    }
  }
}
```

### ANSWER_EVALUATION_COMPLETED (32,922 occurrences)

**Total Fields:** 48  
**Common Fields:** 35  
**Occasional Fields:** 0  
**Rare Fields:** 13

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `self_evaluation` - Self evaluation
- `evaluation_reason` - Evaluation reason

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "ANSWER_EVALUATION_COMPLETED"}},
        {"exists": {"field": "self_evaluation"}}
      ]
    }
  }
}
```

### FULL_CONVERSATION_PREPARED (32,343 occurrences)

**Total Fields:** 41  
**Common Fields:** 38  
**Occasional Fields:** 3  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `history` - Conversation history

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "FULL_CONVERSATION_PREPARED"}},
        {"exists": {"field": "history"}}
      ]
    }
  }
}
```

### KNOWLEDGE_FETCHED (32,229 occurrences)

**Total Fields:** 42  
**Common Fields:** 41  
**Occasional Fields:** 0  
**Rare Fields:** 1

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `document_id` - Document ID
- `url` - Document URL
- `collection_id` - Collection ID
- `score` - Relevance score
- `search_metric` - Search metric
- `keywords` - Keywords

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "KNOWLEDGE_FETCHED"}},
        {"exists": {"field": "document_id"}}
      ]
    }
  }
}
```

### RETURNING_CLEANED_ANSWER (28,758 occurrences)

**Total Fields:** 41  
**Common Fields:** 38  
**Occasional Fields:** 3  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `languageModel` - LLM model

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "RETURNING_CLEANED_ANSWER"}}
      ]
    }
  }
}
```

### RESOLVED_DETECTION_COMPLETED (24,881 occurrences)

**Total Fields:** 41  
**Common Fields:** 38  
**Occasional Fields:** 3  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `markedResolved` - Resolution flag (boolean)

**Critical Field:** `markedResolved` indicates resolution decision

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "RESOLVED_DETECTION_COMPLETED"}},
        {"term": {"markedResolved": true}}
      ]
    }
  }
}
```

### AB_EXPERIMENT_RETRIEVED (12,122 occurrences)

**Total Fields:** 43  
**Common Fields:** 38  
**Occasional Fields:** 5  
**Rare Fields:** 0

**Typical Fields (100% presence):**
- `time`, `conversationId`, `turnId`, `k8s_version`
- `ab_experiment_variant` - A/B test variant (LEGACY, SUPERVISOR, etc.)
- `ab_experiment` - Experiment identifier
- `experiment_context` - Experiment context

**Critical Field:** `ab_experiment_variant` is the **primary A/B test field**

**Query Example:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "AB_EXPERIMENT_RETRIEVED"}},
        {"exists": {"field": "ab_experiment_variant"}}
      ]
    }
  }
}
```

---

## Field-to-Event Mapping

### Most Common Fields Across Events

| Field | Appears In Events | Primary Usage |
|-------|-------------------|---------------|
| `time` | 44 | Universal timestamp |
| `conversationId` | 44 | Conversation correlation |
| `k8s_version` | 44 | Infrastructure tracking |
| `message` | 44 | Log messages |
| `channelId` | 44 | Channel identification |
| `@timestamp` | 44 | OpenSearch timestamp |
| `cicd` | 44 | CI/CD tracking |
| `k8s_name` | 44 | Service name |
| `k8s_image` | 44 | Container image |
| `k8s_container` | 44 | Container name |

### Event-Specific Fields (Appear in Single Event Only)

These fields are unique to specific events and are critical for those event types:

| Field | Event | Description |
|-------|-------|-------------|
| `response_status` | RESPONSE_RETURNED | Completion status |
| `ab_experiment_variant` | AB_EXPERIMENT_RETRIEVED | A/B test variant |
| `markedForAgentHandover` | AGENT_HANDOVER_DETECTION_COMPLETED | Handover flag |
| `markedResolved` | RESOLVED_DETECTION_COMPLETED | Resolution flag |
| `function_status` | FUNCTION_CALL_COMPLETED | Function execution status |
| `classifier-selected-agent` | CLASSIFICATION_*_DONE | Selected agent |
| `transcript` | TRANSCRIPT_PREPARED | Conversation transcript |
| `history` | FULL_CONVERSATION_PREPARED | Conversation history |
| `document_id` | KNOWLEDGE_FETCHED | Knowledge document |

---

## Event Correlation Strategy

### Events with Common Fields for Correlation

**Primary Correlation Keys:**
- `conversationId` + `turnId` - Appear in all events
- `traceId` + `spanId` - Distributed tracing
- `correlationId` - Request correlation

**Event Pairs Requiring Correlation:**

1. **A/B Test + Completion Status:**
   - `AB_EXPERIMENT_RETRIEVED` (has `ab_experiment_variant`)
   - `RESPONSE_RETURNED` (has `response_status`)
   - **Correlation:** Use `conversationId` + `turnId`

2. **Function Call + Function Result:**
   - `FUNCTION_CALLED` (has `function`, `phase`, `input`)
   - `FUNCTION_CALL_COMPLETED` (has `function_status`, `function_output`)
   - **Correlation:** Use `conversationId` + `turnId` + `function`

3. **Agent Selection + Agent Usage:**
   - `CLASSIFICATION_*_DONE` (has `classifier-selected-agent`)
   - `LLM_STARTED` / `LLM_COMPLETED` (has `agent`)
   - **Correlation:** Use `conversationId` + `turnId`

4. **Intent Detection + Intent Routing:**
   - `INTENT_DETECTION_COMPLETED` (has `intent_json`, `category`)
   - `INTENT_TRAFFIC_SPLIT` (has `detectedIntent`)
   - **Correlation:** Use `conversationId` + `turnId`

---

## Query Building Patterns

### Pattern 1: Query by Event Type with Specific Fields

```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "<EVENT_TYPE>"}},
        {"exists": {"field": "<FIELD_NAME>"}}
      ]
    }
  }
}
```

### Pattern 2: Query Multiple Events with Common Field

```json
{
  "query": {
    "bool": {
      "must": [
        {"terms": {"event.keyword": ["<EVENT1>", "<EVENT2>"]}},
        {"exists": {"field": "<COMMON_FIELD>"}}
      ]
    }
  }
}
```

### Pattern 3: Correlate Events Using Common Keys

**Step 1:** Query Event A
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "<EVENT_A>"}},
        {"exists": {"field": "<FIELD_A>"}}
      ]
    }
  }
}
```

**Step 2:** Query Event B and join in application
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event.keyword": "<EVENT_B>"}},
        {"terms": {"conversationId.keyword": ["<conv_ids_from_event_a>"]}},
        {"terms": {"turnId.keyword": ["<turn_ids_from_event_a>"]}}
      ]
    }
  }
}
```

---

## Recommendations

### 1. Always Include Universal Fields

When querying any event, include filters on:
- `@timestamp` - Date range
- `conversationId` / `turnId` - For correlation
- `k8s_name` / `k8s_container` - For service filtering

### 2. Use Event-Specific Fields

For event-specific queries:
- Check this document for typical fields
- Use event-specific fields for filtering
- Include common fields for correlation

### 3. Correlation Strategy

- Use `conversationId` + `turnId` as primary correlation keys
- For A/B test analysis: Query `AB_EXPERIMENT_RETRIEVED` and `RESPONSE_RETURNED` separately, then join
- For function analysis: Query both `FUNCTION_CALLED` and `FUNCTION_CALL_COMPLETED`

### 4. Field Presence Patterns

- **Common (80%+):** Always present, safe to use
- **Occasional (20-80%):** Check existence before use
- **Rare (<20%):** May not be reliable, validate before use

---

## Complete Event List

All 44 event types analyzed:

1. LLM_COMPLETED
2. MEMORY_STORE_EVENT
3. LLM_STARTED
4. CHAT_REQUEST_PROCESSING_STARTED
5. RESPONSE_RETURNED
6. RECEIVED_CHAT_MESSAGE
7. RESPONSE_GENERATION_COMPLETED
8. TRANSCRIPT_PREPARED
9. USECASE_PROMPT_IDENTIFIED
10. FUNCTION_CALLED
11. FUNCTION_CALL_COMPLETED
12. USER_PROFILE_UPDATED
13. INTENT_DETECTION_COMPLETED
14. BLACKLIST_CHECKED
15. INTENT_TRAFFIC_SPLIT
16. CLASSIFICATION_VECTOR_DONE
17. CLASSIFICATION_VECTOR_METRICS
18. AGENT_HANDOVER_DETECTION_COMPLETED
19. CLASSIFICATION_FASTTRACK_DONE
20. CLASSIFICATION_LLM_DONE
21. ANSWER_EVALUATION_COMPLETED
22. FULL_CONVERSATION_PREPARED
23. KNOWLEDGE_FETCHED
24. RETURNING_CLEANED_ANSWER
25. RESOLVED_DETECTION_COMPLETED
26. RECEIVED_TURN_MESSAGE
27. EXECUTION_TYPE
28. AB_EXPERIMENT_RETRIEVED
29. DISAMBIGUATION_DONE
30. REPHRASE_COMPLETED
31. SUPERVISOR_FLOW_INITIATED
32. SUPERVISOR_PLANNER_TIME_TAKEN
33. PLANNER_RESPONSE_RECEIVED
34. SUPERVISOR_OVERRIDDEN_HISTORY
35. SMS_ACCEPTED
36. TURN_RESPONSE_RETURNED
37. CALL_HANGUP
38. HALLUCINATION_CHECKED
39. SMS_SEND_INITIATED
40. SUPERVISOR_DISAMBIGUATION_DECISION
41. ANONY_TOKEN_IN_ANSWER
42. transaction
43. conversation_end
44. conversation_init

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-31  
**Related Documents:** `logs_analysis.md`, `logs_broad_exploration.md`, `logs_system_prompt.md`, `event_field_relationships.json`

