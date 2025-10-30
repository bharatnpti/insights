# OpenSearch Logs Deep Analysis

**Generated:** 2025-10-31  
**Index:** `ia-platform-prod-*`  
**Date Range:** 2025-10-27 to 2025-10-30  
**Analysis Type:** Comprehensive Field Discovery and Categorization

---

## Executive Summary

This analysis explores OpenSearch logs from a multi-agent chatbot platform to understand field structures, event types, and data patterns. The goal is to enable generic natural language requirement processing for data extraction and analysis.

### Key Findings

- **Total Fields Discovered:** 123 unique fields
- **Event Types Analyzed:** 44 different event types
- **Sample Documents:** 90+ documents analyzed across different event types
- **Field Categories:** 7 major categories identified

---

## Field Categories

### 1. Completion-Related Fields (8 fields)

These fields indicate the status or outcome of conversations/turns:

| Field | Type | Description | Sample Values |
|-------|------|-------------|---------------|
| `response_status` | string | **Primary completion status indicator** | ONGOING, RESOLVED, UNRESOLVED, AGENT_HANDOVER, AUTHORIZATION_REQUIRED, CALL_HANGUP, INSUFFICIENT_PERMISSIONS |
| `markedForAgentHandover` | boolean | Flag indicating handover to human agent | true, false |
| `markedResolved` | boolean | Flag indicating conversation resolution | true/false |
| `unresolved_reason` | string | Reason for unresolved conversations | Various reasons |
| `function_status` | string | Status of function calls | success, error, etc. |
| `result` | string | General result field | Various result strings |
| `completionTokens` | string | Number of completion tokens used | "39", "11", "3", "4", etc. |
| `classifier-embedding-search-result` | string | Classifier search result | Various results |

**Key Insight:** `response_status` is the most reliable field for determining completion status with 7 distinct values:
- **ONGOING**: 169,353 occurrences (80.4%)
- **AGENT_HANDOVER**: 27,299 occurrences (13.0%)
- **RESOLVED**: 5,028 occurrences (2.4%)
- **AUTHORIZATION_REQUIRED**: 4,219 occurrences (2.0%)
- **UNRESOLVED**: 3,892 occurrences (1.8%)
- **CALL_HANGUP**: 334 occurrences (0.2%)
- **INSUFFICIENT_PERMISSIONS**: 317 occurrences (0.2%)

---

### 2. Conversation-Related Fields (10 fields)

Fields that identify and track conversations:

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `conversationId` | string | Primary conversation identifier (UUID format) | Most common identifier |
| `turnId` | string | Turn identifier within a conversation | Used for turn-level analysis |
| `conversation_id` | string | Alternative conversation ID format | Used in some event types |
| `turn_id` | string | Alternative turn ID format | Used in some event types |
| `messages` | string/array | Conversation messages | Contains user and assistant messages |
| `message` | string | Log message content | General log message field |
| `conversation` | string | Serialized conversation object | Contains UserMessage/AssistantMessage arrays |
| `returnUseCaseId` | string | Use case identifier | Links to specific use cases |
| `function_error_message` | string | Error messages from function calls | Error tracking |
| `classifier-user-message` | string | User message from classifier | User input in classifier context |

**Usage Patterns:**
- Most events use `conversationId` and `turnId` (camelCase)
- Some legacy events use `conversation_id` and `turn_id` (snake_case)
- Both formats can appear in the same index

---

### 3. A/B Test-Related Fields (5 fields)

Fields related to A/B testing and experimentation:

| Field | Type | Description | Sample Values |
|-------|------|-------------|---------------|
| `ab_experiment_variant` | string | **Primary A/B test variant field** | LEGACY, SUPERVISOR, false |
| `ab_experiment` | string | A/B experiment name | onebot.platform.experiment.executor |
| `variant` | string | General variant field | "" (empty), "beta" |
| `experiment_context` | string | Context of the experiment | "platform" |
| `isAppDeeplinksEnabled` | string | Feature flag | true/false |

**Key Insight:** 
- `ab_experiment_variant` contains the actual experiment variant (LEGACY, SUPERVISOR)
- Found in `AB_EXPERIMENT_RETRIEVED` events
- 12,082 occurrences in the analyzed period
- Always appears with `ab_experiment` field containing the experiment name

---

### 4. Status Fields (6 fields)

Fields indicating various statuses:

| Field | Type | Description | Sample Values |
|-------|------|-------------|---------------|
| `response_status` | string | Response completion status | ONGOING, RESOLVED, UNRESOLVED, AGENT_HANDOVER, etc. |
| `function_status` | string | Function call status | success, error, etc. |
| `step` | string | Processing step | LmosAgent, LoadCustomerProfile, GenerateFlexCards, ClassifyIntentCategory, RouteToAgentBasedOnIntent, etc. |
| `phase` | string | Processing phase | Generating, FilterOutput, generatePrompt, FilterInput |
| `level` | string | Log level | INFO, DEBUG, ERROR, WARN |
| `authLevel` | string | Authentication level | Various auth levels |

**Most Common Steps:**
1. LmosAgent: 3,197,720 occurrences
2. LoadCustomerProfile: 1,340,225 occurrences
3. GenerateFlexCards: 1,084,704 occurrences
4. ClassifyIntentCategory: 642,613 occurrences
5. UseCaseResponseHandler: 629,410 occurrences

---

### 5. Temporal Fields (7 fields)

Fields related to time and timing:

| Field | Type | Description | Usage |
|-------|------|-------------|-------|
| `@timestamp` | string | **Primary timestamp field** | ISO 8601 format, used for all time-based queries |
| `time` | string | Alternative timestamp | Used in some events |
| `log_entry_timestamp` | string | Log entry specific timestamp | For specific log entries |
| `responseTime` | string | Response time measurement | Performance metric |
| `responseTimeInMs` | string | Response time in milliseconds | Performance metric |
| `rendered_template` | string | Timestamp in template context | Template-related timing |

**Key Insight:** `@timestamp` is the standard field for time-based filtering in OpenSearch queries.

---

### 6. Identifier Fields (30 fields)

Fields used for identification, correlation, and tracking:

| Field | Description |
|-------|-------------|
| `conversationId`, `conversation_id` | Conversation identifiers |
| `turnId`, `turn_id` | Turn identifiers |
| `traceId`, `trace_id` | Distributed tracing identifiers |
| `spanId`, `span_id` | Span identifiers for tracing |
| `correlationId`, `correlation_id`, `x-correlation-id` | Correlation IDs |
| `vaspConnId` | VASP connection identifier |
| `referrerId` | Referrer identifier |
| `featureId` | Feature identifier |
| `log_entry_id` | Log entry identifier |
| `customerFeedbackId` | Customer feedback identifier |
| `tenantId`, `tenant` | Tenant identifiers |
| `channelId`, `channel_id` | Channel identifiers |
| `sourceChannelId` | Source channel identifier |
| `returnUseCaseId` | Use case identifier |
| `application_id` | Application identifier |
| `document_id`, `collection_id` | Document/collection identifiers |
| `cms_tenant_id` | CMS tenant identifier |
| `provider_name` | Provider name identifier |

**Correlation Strategy:** 
- Use `conversationId` + `turnId` for turn-level correlation
- Use `traceId` for distributed tracing across services
- Use `correlationId` for request correlation

---

### 7. Metadata Fields (12 fields)

Infrastructure and environment metadata:

| Field | Description | Sample Values |
|-------|-------------|---------------|
| `k8s_name` | Kubernetes service name | ia-platform, anonymization-service, search-service |
| `k8s_namespace` | Kubernetes namespace | oneai-platform |
| `k8s_pod` | Kubernetes pod name | ia-platform-74c6dc676c-btgtt |
| `k8s_host` | Kubernetes host | ip-172-21-213-241.eu-central-1.compute.internal |
| `k8s_container` | Container name | ia-platform, istio-proxy, anonymization-service |
| `k8s_version` | Kubernetes version | Various version strings |
| `k8s_image` | Container image | SHA256 hashes |
| `cicd` | CI/CD service name | ia-platform, anonymization-service |
| `cicd-pipeline` | CI/CD pipeline ID | 52351366-283407142 |
| `environment` | Environment name | live,logformat-json |
| `tenant`, `tenantId` | Tenant information | de (Germany) |
| `usecase_version` | Use case version | Version strings |

**Key Services:**
- **ia-platform**: 14,492,066 occurrences (main platform)
- **anonymization-service**: 3,989,538 occurrences
- **search-service**: 1,634,069 occurrences
- **contract-agent-service**: 470,919 occurrences
- **flexcard-agent-service**: 419,565 occurrences

---

## Event Types Analysis

### Top 20 Event Types by Occurrence

| Event Type | Occurrences | Description | Key Fields |
|------------|-------------|-------------|------------|
| LLM_COMPLETED | 614,445 | Large Language Model completion event | conversationId, turnId, responseTime, completionTokens, totalTokens, prompt, messages |
| MEMORY_STORE_EVENT | 285,540 | Memory storage event | key, value, agent, vaspConnId |
| LLM_STARTED | 263,022 | LLM processing start | conversationId, turnId, languageModel, step |
| CHAT_REQUEST_PROCESSING_STARTED | 217,231 | Chat request processing initiation | conversationId, turnId, question, agent |
| RESPONSE_RETURNED | 210,103 | Response returned to user | **response_status**, conversationId, turnId, message |
| RECEIVED_CHAT_MESSAGE | 208,360 | Incoming chat message received | conversationId, turnId, customerFeedbackId |
| RESPONSE_GENERATION_COMPLETED | 203,799 | Response generation finished | conversationId, turnId, message |
| TRANSCRIPT_PREPARED | 173,586 | Transcript prepared | conversationId, turnId, transcript |
| USECASE_PROMPT_IDENTIFIED | 141,501 | Use case prompt identified | conversationId, turnId, returnUseCaseId, usecase_version |
| FUNCTION_CALLED | 96,018 | Function called | conversationId, turnId, function, input, variant |
| FUNCTION_CALL_COMPLETED | 96,012 | Function call completed | conversationId, turnId, function, function_status, function_output |
| USER_PROFILE_UPDATED | 86,280 | User profile update | conversationId, turnId, user_profile |
| INTENT_DETECTION_COMPLETED | 75,796 | Intent detection finished | conversationId, turnId, detectedIntent, category, subCategory |
| BLACKLIST_CHECKED | 46,890 | Blacklist check performed | conversationId, turnId, agent |
| INTENT_TRAFFIC_SPLIT | 45,229 | Intent traffic splitting | conversationId, turnId, detectedIntent, explicitIntent |
| AGENT_HANDOVER_DETECTION_COMPLETED | 43,442 | Agent handover detection finished | conversationId, turnId, **markedForAgentHandover** |
| CLASSIFICATION_VECTOR_METRICS | 43,423 | Classification vector metrics | conversationId, turnId, classifier-embedding-ranking-* |
| CLASSIFICATION_VECTOR_DONE | 43,422 | Classification vector completion | conversationId, turnId, classifier-selected-agent, classifier-user-message |
| CLASSIFICATION_FASTTRACK_DONE | 43,365 | Fast track classification done | conversationId, turnId, classifier-is-fasttrack |
| CLASSIFICATION_LLM_DONE | 43,048 | LLM-based classification done | conversationId, turnId, classifier-candidate-agents |

### A/B Test Events

| Event Type | Occurrences | Key Fields |
|------------|-------------|------------|
| AB_EXPERIMENT_RETRIEVED | 12,082 | **ab_experiment_variant**, ab_experiment, experiment_context, conversationId, turnId |

---

## Field Value Analysis

### Critical Field Value Distributions

#### response_status Values

| Value | Count | Percentage | Meaning |
|-------|-------|------------|---------|
| ONGOING | 169,353 | 80.4% | Conversation still in progress |
| AGENT_HANDOVER | 27,299 | 13.0% | Handed over to human agent |
| RESOLVED | 5,028 | 2.4% | Successfully resolved |
| AUTHORIZATION_REQUIRED | 4,219 | 2.0% | Requires authorization |
| UNRESOLVED | 3,892 | 1.8% | Ended without resolution |
| CALL_HANGUP | 334 | 0.2% | Call was hung up |
| INSUFFICIENT_PERMISSIONS | 317 | 0.2% | Insufficient permissions |

**Total:** 210,442 events with response_status

#### markedForAgentHandover Values

| Value | Count | Percentage |
|-------|-------|------------|
| false | 35,014 | 80.6% |
| true | 8,429 | 19.4% |

**Total:** 43,443 events with markedForAgentHandover

#### ab_experiment_variant Values

| Value | Count | Description |
|-------|-------|-------------|
| LEGACY | ~8,500 | Legacy experiment variant |
| SUPERVISOR | ~960 | Supervisor experiment variant |
| false | Various | Not in experiment |

**Note:** Actual counts vary by date range. From analysis: ~9,464 valid A/B test events.

#### variant Values (General)

| Value | Count | Percentage |
|-------|-------|------------|
| "" (empty) | 2,250,630 | 99.5% |
| "beta" | 11,673 | 0.5% |

**Note:** This is different from `ab_experiment_variant`. The general `variant` field is mostly empty.

---

## Field Correlation Patterns

### Correlation Key: conversationId + turnId

**Most reliable correlation strategy:**
- Use `conversationId` + `turnId` together to correlate events
- Both fields appear in most event types
- Alternative formats (`conversation_id`, `turn_id`) may appear in legacy events

### Event Sequence Pattern

Typical conversation flow:
1. `RECEIVED_CHAT_MESSAGE` → User message received
2. `CHAT_REQUEST_PROCESSING_STARTED` → Processing begins
3. `USECASE_PROMPT_IDENTIFIED` → Use case determined
4. `LLM_STARTED` → LLM processing begins
5. `LLM_COMPLETED` → LLM processing completes
6. `RESPONSE_GENERATION_COMPLETED` → Response generated
7. `RESPONSE_RETURNED` → **Response with `response_status`** → Response returned

### A/B Test Correlation

**Pattern:**
1. `AB_EXPERIMENT_RETRIEVED` event contains:
   - `ab_experiment_variant`: LEGACY or SUPERVISOR
   - `conversationId` and `turnId`
2. To find completion status:
   - Look for `RESPONSE_RETURNED` events with same `conversationId` + `turnId`
   - The `response_status` field contains the completion status

**Challenge:** Not all A/B test events have corresponding RESPONSE_RETURNED events due to:
- Different event timing
- Different indices potentially
- Event routing differences

---

## Query Patterns for Common Requirements

### Finding A/B Test Data

```json
{
  "query": {
    "bool": {
      "must": [
        {"exists": {"field": "ab_experiment_variant"}},
        {"range": {
          "@timestamp": {
            "gte": "2025-10-27T00:00:00",
            "lte": "2025-10-30T23:59:59"
          }
        }}
      ]
    }
  }
}
```

### Finding Completion Status

```json
{
  "query": {
    "bool": {
      "must": [
        {"exists": {"field": "response_status"}},
        {"range": {
          "@timestamp": {
            "gte": "2025-10-27T00:00:00",
            "lte": "2025-10-30T23:59:59"
          }
        }}
      ]
    }
  }
}
```

### Correlating A/B Test with Completion Status

**Strategy 1: Direct correlation by turnId**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"conversationId": "<conversation-id>"}},
        {"term": {"turnId": "<turn-id>"}},
        {"terms": {"event": ["AB_EXPERIMENT_RETRIEVED", "RESPONSE_RETURNED"]}}
      ]
    }
  }
}
```

**Strategy 2: Separate queries and join in application**
1. Query all A/B test events
2. Query all response_status events
3. Join on `conversationId` + `turnId` in pandas/application logic

---

## Field Naming Patterns

### CamelCase vs snake_case

**CamelCase (most common):**
- `conversationId`, `turnId`, `traceId`, `spanId`, `correlationId`

**snake_case (less common, legacy):**
- `conversation_id`, `turn_id`, `trace_id`, `span_id`, `correlation_id`

**Recommendation:** Query both formats when searching for identifiers.

### Prefix Patterns

- **k8s_***: Kubernetes infrastructure fields
- **cicd***: CI/CD related fields
- **classifier-***: Classification/ML related fields
- **function_***: Function call related fields
- **log_entry_***: Log entry specific fields

---

## Data Quality Observations

### Coverage Statistics

- **A/B Test Events with completion status correlation:** ~6.7% (637 out of 9,464)
  - ONGOING: 484 events (5.1%)
  - AGENT_HANDOVER: 107 events (1.1%)
  - RESOLVED: 27 events (0.3%)
  - UNRESOLVED: 19 events (0.2%)
  - UNKNOWN: 8,827 events (93.3%)

### Data Gaps

1. **Low correlation rate:** Most A/B test events don't have corresponding response_status events
   - Possible reasons:
     - Different event timing
     - Different services emitting events
     - Different indices or routing
   
2. **Field format inconsistencies:**
   - Mix of camelCase and snake_case
   - Both formats may appear in same index
   
3. **Missing fields:**
   - Not all events have all fields
   - Some fields only appear in specific event types

---

## Recommendations for Generic NL Processing

### 1. Field Mapping Strategy

Create a field mapping dictionary that maps natural language terms to actual field names:

```python
FIELD_MAPPINGS = {
    "completion": ["response_status", "markedResolved", "markedForAgentHandover"],
    "status": ["response_status", "function_status", "step", "phase"],
    "conversation": ["conversationId", "conversation_id"],
    "turn": ["turnId", "turn_id"],
    "variant": ["ab_experiment_variant", "variant"],
    "experiment": ["ab_experiment", "ab_experiment_variant"],
    "resolved": ["response_status=RESOLVED", "markedResolved=true"],
    "unresolved": ["response_status=UNRESOLVED"],
    "handover": ["response_status=AGENT_HANDOVER", "markedForAgentHandover=true"],
    "ongoing": ["response_status=ONGOING"],
    "timestamp": ["@timestamp", "time"],
    "date": ["@timestamp"],
    "time": ["@timestamp", "responseTime", "time"]
}
```

### 2. Query Building Strategy

1. **Parse natural language requirement**
2. **Identify key entities:**
   - What: A/B test, completion status, conversations, turns
   - When: Date ranges, time periods
   - How: Count, percentage, correlation
3. **Map to fields:**
   - Use FIELD_MAPPINGS to find relevant fields
   - Check field_value_analysis for value patterns
4. **Build OpenSearch query:**
   - Use appropriate query types (term, terms, range, exists)
   - Handle both camelCase and snake_case variants
5. **Execute and correlate:**
   - Execute queries
   - Join results in application if needed
   - Calculate aggregations (counts, percentages, cross-tabulations)

### 3. Event Type Filtering

Use event types to filter relevant documents:
- A/B test analysis: Filter for `AB_EXPERIMENT_RETRIEVED`
- Completion analysis: Filter for `RESPONSE_RETURNED`
- Correlation: Include both event types in query

### 4. Correlation Strategy

**Primary:** Use `conversationId` + `turnId` for turn-level correlation  
**Secondary:** Use `traceId` for distributed tracing across services  
**Fallback:** Use `correlationId` for request-level correlation

---

## Technical Notes

### OpenSearch Query Best Practices

1. **Use exists queries for field presence:**
   ```json
   {"exists": {"field": "ab_experiment_variant"}}
   ```

2. **Use term queries for exact matches:**
   ```json
   {"term": {"event.keyword": "RESPONSE_RETURNED"}}
   ```

3. **Use terms for multiple values:**
   ```json
   {"terms": {"response_status": ["RESOLVED", "UNRESOLVED", "AGENT_HANDOVER"]}}
   ```

4. **Use range for timestamps:**
   ```json
   {"range": {"@timestamp": {"gte": "2025-10-27T00:00:00", "lte": "2025-10-30T23:59:59"}}}
   ```

### Pagination

- OpenSearch limits to 10,000 results by default
- Use `from` and `size` for pagination
- For large result sets, consider using scroll API (if permissions allow)

### Field Type Handling

- Most fields are strings in the documents
- Use `.keyword` suffix for exact term queries
- Try both with and without `.keyword` suffix if term queries fail

---

## Event Type Field Summaries

### RESPONSE_RETURNED (Most Important for Completion Status)

**Typical Fields:**
- `response_status` (PRIMARY completion indicator)
- `conversationId`, `turnId`
- `message`, `logger_name`, `thread_name`
- `@timestamp`, `time`
- `traceId`, `spanId`, `correlationId`
- Infrastructure: `k8s_*`, `cicd*`, `application_id`, `environment`

### AB_EXPERIMENT_RETRIEVED (A/B Test Events)

**Typical Fields:**
- `ab_experiment_variant` (LEGACY, SUPERVISOR)
- `ab_experiment` (experiment name)
- `experiment_context` ("platform")
- `conversationId`, `turnId`
- `evaluation_reason`, `provider_name`, `cms_tenant_id`
- Infrastructure fields

### LLM_COMPLETED (Performance Metrics)

**Typical Fields:**
- `conversationId`, `turnId`
- `responseTime`, `completionTokens`, `promptTokens`, `totalTokens`
- `prompt`, `messages`, `input`
- `languageModel`, `model`
- `step`, `agent`

### AGENT_HANDOVER_DETECTION_COMPLETED

**Typical Fields:**
- `markedForAgentHandover` (boolean)
- `conversationId`, `turnId`
- `log_entry_id`, `log_entry_timestamp`

---

## Usage Examples

### Example 1: A/B Test Analysis

**Natural Language:** "Show A/B test variant distribution with completion statuses for last 4 days"

**Processing Steps:**
1. Identify: A/B test (`ab_experiment_variant`), completion (`response_status`), time range (last 4 days)
2. Query A/B test events
3. Query completion status events
4. Correlate on `conversationId` + `turnId`
5. Generate cross-tabulation (variant × completion_status)
6. Calculate percentages

**Output:** CSV with variant, completion_status, count, percentage

### Example 2: Turn-Level Analysis

**Natural Language:** "Analyze turn-level data with variants and whether turns were resolved"

**Processing Steps:**
1. Extract all turns with A/B test variants
2. Find corresponding completion status for each turn
3. Create turn-level dataset
4. Aggregate by variant and status

---

## Conclusion

This analysis provides a comprehensive understanding of OpenSearch log structure for the multi-agent chatbot platform. The key insights enable:

1. **Generic query building** from natural language requirements
2. **Field mapping** between user terminology and actual field names
3. **Correlation strategies** for joining related events
4. **Data quality understanding** to set appropriate expectations

The `field_documentation.json` file contains machine-readable field metadata that can be used to build automated query generation systems.

---

## Appendix: Complete Field List

### All 123 Fields Discovered

**Completion Related:**
result, completionTokens, response_status, unresolved_reason, function_status, markedForAgentHandover, classifier-embedding-search-result, markedResolved

**Conversation Related:**
conversationId, messages, message, returnUseCaseId, turnId, conversation, function_error_message, classifier-user-message, conversation_id, turn_id

**A/B Test Related:**
isAppDeeplinksEnabled, variant, experiment_context, ab_experiment_variant, ab_experiment

**Status Related:**
step, authLevel, level, phase, response_status, function_status

**Temporal:**
responseTime, @timestamp, time, responseTimeInMs, log_entry_timestamp, rendered_template, classifier-candidate-agents

**Identifiers:**
conversationId, totalTokens, tenantId, application_id, returnUseCaseId, vaspConnId, spanId, sourceChannelId, correlationId, channelId, completionTokens, traceId, turnId, promptTokens, referrerId, featureId, key, log_entry_id, customerFeedbackId, x-correlation-id, classifier-candidate-agents, keywords, document_id, collection_id, trace_id, span_id, conversation_id, turn_id, cms_tenant_id, provider_name

**Metadata:**
tenantId, k8s_version, k8s_namespace, application_id, environment, sourceChannelId, channelId, tenant, usecase_version, cms_tenant_id, experiment_context

**Infrastructure:**
cicd, cicd-pipeline, k8s_pod, k8s_host, k8s_name, k8s_version, k8s_image, k8s_container, k8s_namespace

**Other:**
logger_name, thread_name, agent, source_intent, languageModel, model, prompt, input, activeFeatures, beta, authTechnicalError, functions, seed, phase, usecase_name, usecase_description, function, function_input, function_output, error, type, product_name, user_profile, intent_json, category, subCategory, detectedIntent, explicitIntent, classifier-embedding-ranking-evaluation, classifier-embedding-ranking-top-agent, classifier-embedding-ranking-thresholds, classifier-selected-agent, classifier-type, classifier-embedding-search-query, classifier-is-fasttrack, self_evaluation, reason, history, url, score, search_metric, executionType, evaluation_reason, natco_code, authMethod, transcript, question, filter, callingAgent, links_offered, link_count, flexcards

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-31
