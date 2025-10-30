# Non-Event Documents Analysis

**Generated:** 2025-10-31  
**Index:** `ia-platform-prod-*`  
**Date Range:** 2025-10-27 to 2025-10-30  
**Analysis Type:** Non-Event Documents Exploration

---

## Executive Summary

This document analyzes documents in OpenSearch logs that **do not have an `event` field**. These documents represent:
- Application logs (INFO, DEBUG, WARN, ERROR)
- Infrastructure logs (istio-proxy, kubernetes)
- Transaction logs
- System logs
- Error logs without structured events

**Key Statistics:**
- **At least 10,000+ non-event documents** in the date range (query limit reached)
- **80 unique fields** discovered in non-event documents
- **Primary types:** Application logs, proxy logs, transaction logs
- **Top containers:** ia-platform, istio-proxy, anonymization-service

---

## Document Count by Category

### By Container

| Container | Document Count | Percentage | Type |
|-----------|---------------|------------|------|
| **ia-platform** | 10,847,484 | ~68% | Application logs |
| **istio-proxy** | 4,962,695 | ~31% | Infrastructure/proxy logs |
| **anonymization-service** | 2,015,047 | ~13% | Service logs |
| **search-service** | 1,191,814 | ~7% | Service logs |
| **contract-agent-service** | 309,263 | ~2% | Agent logs |
| **oneai-chat-bff** | 270,109 | ~1.7% | BFF logs |
| **invoice-agent-service** | 200,018 | ~1.3% | Agent logs |
| **ivr-billing-agent-service** | 170,684 | ~1.1% | Agent logs |
| **tks-agent-service** | 117,293 | ~0.7% | Agent logs |
| **sim-agent-service** | 109,614 | ~0.7% | Agent logs |

**Key Insight:** 
- **ia-platform** contains most application logs (68%)
- **istio-proxy** contains infrastructure/proxy access logs (31%)
- Specialized services have fewer non-event logs

### By Log Level

| Level | Document Count | Percentage | Purpose |
|-------|---------------|------------|---------|
| **INFO** | 15,376,116 | ~92% | Informational logs |
| **DEBUG** | 171,449 | ~1% | Debug logs |
| **WARN** | 79,073 | ~0.5% | Warning logs |
| **ERROR** | 35,672 | ~0.2% | Error logs |
| **info** (lowercase) | 20,677 | ~0.1% | Info logs (alternative format) |
| **error** (lowercase) | 15,294 | ~0.1% | Error logs (alternative format) |
| **WARNING** | 978 | <0.01% | Warning logs |
| **warning** | 346 | <0.01% | Warning logs |
| **warn** | 268 | <0.01% | Warning logs |
| **fatal** | 4 | <0.01% | Fatal logs |

**Key Insight:**
- **92% are INFO logs** (standard application logging)
- **ERROR logs are rare** (~0.2%), but critical for debugging
- **Multiple level formats** exist (INFO/info, ERROR/error, WARN/warn/warning)

### By Service

| Service | Document Count | Type |
|---------|---------------|------|
| **ia-platform** | 12,465,070 | Main platform |
| **anonymization-service** | 4,035,573 | Support service |
| **search-service** | 1,651,952 | Support service |
| **contract-agent-service** | 364,312 | Agent service |
| **oneai-chat-bff** | 328,292 | Backend for frontend |
| **invoice-agent-service** | 254,584 | Agent service |
| **ivr-billing-agent-service** | 198,158 | Agent service |
| **search-service-beta** | 193,332 | Beta service |
| **order-agent-service** | 147,011 | Agent service |
| **sim-agent-service** | 146,853 | Agent service |

**Key Insight:**
- **Main platform** (ia-platform) dominates with 78% of non-event documents
- **Support services** (anonymization, search) have significant log volumes
- **Agent services** have moderate log volumes

### By Logger

| Logger Name | Document Count | Purpose |
|------------|---------------|---------|
| **DialogControllerV2** | 876,542 | Request handling |
| **DefaultConversationHandler** | 846,461 | Conversation processing |
| **ModelResolver** | 783,883 | Model resolution |
| **LmosAgent** | 764,207 | Agent execution |
| **PurgeConversation** | 595,591 | Conversation cleanup |
| **transactionLogger** | 537,809 | Transaction logging |
| **CustomerProfileRetriever** | 515,227 | Customer data retrieval |
| **LoadCustomerProfile** | 475,954 | Profile loading |
| **OpenAIClientImpl** | 470,609 | OpenAI API calls |
| **Messages** | 405,841 | Message processing |

**Key Insight:**
- **Top loggers** are core platform components (controllers, handlers, agents)
- **Transaction logging** is significant (537K documents)
- **API client logging** (OpenAI) shows external API interactions

---

## Common Fields in Non-Event Documents

### Universal Fields (100% presence)

These fields appear in **all non-event documents** (sampled):

| Field | Description | Usage |
|-------|-------------|-------|
| `k8s_namespace` | Kubernetes namespace | Infrastructure tracking |
| `k8s_version` | Kubernetes version | Version tracking |
| `k8s_name` | Kubernetes service name | Service identification |
| `cicd` | CI/CD service name | Deployment tracking |
| `k8s_pod` | Pod name | Pod identification |
| `k8s_host` | Host machine | Infrastructure tracking |
| `@timestamp` | OpenSearch timestamp | Default temporal field |
| `cicd-pipeline` | CI/CD pipeline ID | Pipeline tracking |
| `k8s_image` | Container image | Container tracking |
| `k8s_container` | Container name | Container identification |

**Usage:** These fields can be used for filtering and grouping across all non-event documents.

### High-Frequency Fields (>50% presence)

| Field | Presence | Description | Usage |
|-------|----------|-------------|-------|
| `time` | 99.1% | Event timestamp | Temporal tracking |
| `message` | 73.0% | Log message | Debugging/observability |
| `level` | 72.7% | Log level | Log severity filtering |
| `correlationId` | 61.3% | Correlation ID | Request correlation |
| `environment` | 54.1% | Environment name | Environment filtering |
| `thread_name` | 54.1% | Thread name | Thread tracking |
| `application_id` | 54.1% | Application ID | Application tracking |
| `logger_name` | 54.1% | Logger name | Logger filtering |
| `turnId` | 50.1% | Turn identifier | Turn-level correlation |
| `conversationId` | 49.7% | Conversation identifier | Conversation correlation |

**Key Insight:**
- **50% of non-event documents** have `conversationId` or `turnId` - can be correlated with event documents
- **`correlationId` appears in 61%** - useful for request tracing
- **`logger_name` appears in 54%** - useful for filtering by component

### Moderate-Frequency Fields (10-50% presence)

| Field | Presence | Description |
|-------|----------|-------------|
| `tenantId` | Variable | Tenant identifier |
| `channelId` | Variable | Channel identifier |
| `traceId` | Variable | Trace identifier |
| `spanId` | Variable | Span identifier |
| `source_intent` | Variable | Source intent |
| `agent` | Variable | Agent identifier |
| `step` | Variable | Processing step |
| `languageModel` | Variable | LLM model |
| `variant` | Variable | A/B test variant |
| `response_status` | Variable | Response status |

**Key Insight:** These fields appear in non-event documents that are related to conversations/events but don't have structured events.

---

## Document Types

### 1. Application Logs (INFO/DEBUG/WARN/ERROR)

**Characteristics:**
- Have `level` field (INFO, DEBUG, WARN, ERROR)
- Have `message` field with log content
- Have `logger_name` field with logger class
- Typically lack `event` field
- Contain `conversationId`/`turnId` if related to conversations

**Example Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"level.keyword": "ERROR"}},
        {"exists": {"field": "conversationId"}}
      ]
    }
  }
}
```

### 2. Infrastructure/Proxy Logs (istio-proxy)

**Characteristics:**
- Container: `istio-proxy`
- No `event` field
- May have HTTP request/response data
- Infrastructure-level logging

**Example Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"k8s_container.keyword": "istio-proxy"}}
      ]
    }
  }
}
```

### 3. Transaction Logs

**Characteristics:**
- Logger: `transactionLogger`
- May have transaction-specific fields
- No `event` field

**Example Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"logger_name.keyword": "transactionLogger"}}
      ]
    }
  }
}
```

### 4. Error Logs (without structured events)

**Characteristics:**
- `level` = ERROR or error
- Have `message` with error content
- May have `conversationId`/`turnId` if related to conversations
- No structured `event` field

**Example Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"terms": {"level.keyword": ["ERROR", "error"]}},
        {"exists": {"field": "conversationId"}}
      ]
    }
  }
}
```

---

## Message Patterns

### Pattern Distribution

| Pattern | Count | Description |
|---------|-------|-------------|
| **other** | 784 | Generic messages |
| **http** | 173 | HTTP-related messages |
| **error** | 15 | Error messages |
| **completion** | 26 | Completion messages |
| **startup** | 2 | Startup messages |

**Key Insight:** Most non-event documents have generic messages, but HTTP and error patterns are significant.

---

## Field Analysis by Category

### Fields by Container

**ia-platform:**
- Common fields: Standard infrastructure + application fields
- Fields: `level`, `message`, `logger_name`, `conversationId`, `turnId`, `agent`, `step`, `languageModel`, `variant`

**istio-proxy:**
- Common fields: Infrastructure-level fields
- Fields: Standard k8s fields, potentially HTTP-related fields

**anonymization-service:**
- Common fields: Service-specific fields
- Fields: Standard k8s fields + service-specific fields

### Fields by Log Level

**INFO:**
- All standard infrastructure fields
- Application-specific fields (`conversationId`, `turnId`, `agent`, `step`)
- Logger and message fields

**ERROR:**
- Same as INFO, but with error-specific content in `message`
- May have stack traces or exception details

**DEBUG:**
- More detailed fields
- Additional debugging information

---

## Correlation Opportunities

### Correlation with Event Documents

**Key:** Many non-event documents can be correlated with event documents using:

1. **`conversationId` + `turnId`** (50% have these fields)
   - Query both event and non-event documents
   - Join on conversationId + turnId

2. **`correlationId`** (61% have this field)
   - Use for request tracing across event and non-event documents

3. **`traceId` + `spanId`** (variable presence)
   - Use for distributed tracing

**Example Correlation Query:**
```python
# Step 1: Get events
event_query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"event.keyword": "LLM_COMPLETED"}},
                {"exists": {"field": "conversationId"}},
                {"exists": {"field": "turnId"}}
            ]
        }
    }
}

# Step 2: Get related non-event logs
non_event_query = {
    "query": {
        "bool": {
            "must": [
                {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
                {"terms": {"conversationId.keyword": ["<from_events>"]}},
                {"terms": {"turnId.keyword": ["<from_events>"]}},
                {"term": {"level.keyword": "ERROR"}}  # Filter for errors
            ]
        }
    }
}
```

---

## Query Patterns

### Pattern 1: Query Non-Event Documents by Container

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"k8s_container.keyword": "ia-platform"}},
        {"term": {"level.keyword": "ERROR"}}
      ]
    }
  }
}
```

### Pattern 2: Query Non-Event Documents by Logger

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"logger_name.keyword": "com.telekom.ia.platform.inbound.customer.DialogControllerV2"}},
        {"exists": {"field": "conversationId"}}
      ]
    }
  }
}
```

### Pattern 3: Query Non-Event Documents by Log Level

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"terms": {"level.keyword": ["ERROR", "WARN"]}},
        {"exists": {"field": "message"}},
        {"range": {"@timestamp": {"gte": "<start>", "lte": "<end>"}}}
      ]
    }
  }
}
```

### Pattern 4: Query Non-Event Documents with Correlation

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"exists": {"field": "conversationId"}},
        {"exists": {"field": "turnId"}},
        {"term": {"level.keyword": "ERROR"}}
      ]
    }
  }
}
```

---

## Recommendations

### 1. Query Strategy

**For Non-Event Documents:**
- Always include `"must_not": [{"exists": {"field": "event"}}]` to exclude event documents
- Filter by `k8s_container` or `k8s_name` for service-specific queries
- Use `level` to filter by log severity
- Use `logger_name` for component-specific queries

**For Event + Non-Event Correlation:**
- Query separately: one for events, one for non-events
- Join on `conversationId` + `turnId` in application
- Use `correlationId` for request-level correlation

### 2. Error Analysis

**For Error Logging:**
- Query non-event documents with `level` = ERROR or error
- Filter by `logger_name` for component-specific errors
- Include `conversationId`/`turnId` for conversation-related errors
- Correlate with event documents to understand context

### 3. Infrastructure Monitoring

**For Infrastructure Logs:**
- Query by `k8s_container` = istio-proxy for proxy logs
- Query by `k8s_name` for service-level aggregation
- Use `k8s_pod` for pod-specific analysis
- Use `k8s_host` for host-level analysis

### 4. Transaction Tracking

**For Transaction Logs:**
- Query by `logger_name` = transactionLogger
- Use `correlationId` for request tracking
- Correlate with event documents using conversationId/turnId

### 5. Debugging

**For Debugging:**
- Query non-event documents with `level` = DEBUG
- Filter by `logger_name` for component-specific debugging
- Include `message` field for detailed log content
- Correlate with event documents to understand flow

---

## Field Comparison: Event vs Non-Event Documents

### Fields Present in Both

| Field | Event Docs | Non-Event Docs | Usage |
|-------|-----------|----------------|-------|
| `conversationId` | 100% | ~50% | Correlation key |
| `turnId` | 100% | ~50% | Correlation key |
| `correlationId` | 100% | ~61% | Request correlation |
| `traceId` | 100% | Variable | Distributed tracing |
| `spanId` | 100% | Variable | Distributed tracing |
| `k8s_*` fields | 100% | 100% | Infrastructure filtering |
| `level` | Rare | ~73% | Log severity (non-events) |
| `message` | 100% | ~73% | Log content |
| `logger_name` | 100% | ~54% | Component filtering |

### Fields Unique to Event Documents

- `event` - Event type
- Event-specific fields (e.g., `response_status`, `ab_experiment_variant`)

### Fields Unique to Non-Event Documents

- `level` - Log level (INFO, ERROR, etc.) - more common in non-events
- `thread_name` - Thread identifier - more common in non-events
- Raw error messages in `message` field

---

## Complete Field List

### Universal Fields (100% in sampled non-event docs)

1. `k8s_namespace`
2. `k8s_version`
3. `k8s_name`
4. `cicd`
5. `k8s_pod`
6. `k8s_host`
7. `@timestamp`
8. `cicd-pipeline`
9. `k8s_image`
10. `k8s_container`

### High-Frequency Fields (>50%)

1. `time` (99.1%)
2. `message` (73.0%)
3. `level` (72.7%)
4. `correlationId` (61.3%)
5. `environment` (54.1%)
6. `thread_name` (54.1%)
7. `application_id` (54.1%)
8. `logger_name` (54.1%)
9. `turnId` (50.1%)
10. `conversationId` (49.7%)

---

## Usage Examples

### Example 1: Find Errors Related to a Conversation

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"conversationId.keyword": "<conversation_id>"}},
        {"terms": {"level.keyword": ["ERROR", "error"]}},
        {"exists": {"field": "message"}}
      ]
    }
  }
}
```

### Example 2: Find All Logs for a Specific Turn

```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"turnId.keyword": "<turn_id>"}},
        {"exists": {"field": "message"}}
      ]
    }
  }
}
```
This query will return both event and non-event documents for the turn.

### Example 3: Find Infrastructure Issues

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"k8s_container.keyword": "istio-proxy"}},
        {"terms": {"level.keyword": ["ERROR", "WARN"]}},
        {"range": {"@timestamp": {"gte": "<start>", "lte": "<end>"}}}
      ]
    }
  }
}
```

### Example 4: Find Transaction Logs for a Request

```json
{
  "query": {
    "bool": {
      "must": [
        {"bool": {"must_not": [{"exists": {"field": "event"}}]}},
        {"term": {"logger_name.keyword": "transactionLogger"}},
        {"term": {"correlationId.keyword": "<correlation_id>"}}
      ]
    }
  }
}
```

---

## Key Takeaways

1. **Significant Volume:** Non-event documents represent a large portion of logs (10K+ minimum, likely millions)

2. **Correlation Capability:** ~50% have `conversationId`/`turnId` - can be correlated with event documents

3. **Primary Types:**
   - Application logs (INFO/ERROR)
   - Infrastructure logs (istio-proxy)
   - Transaction logs

4. **Query Strategy:**
   - Always exclude events: `"must_not": [{"exists": {"field": "event"}}]`
   - Filter by container, service, level, logger
   - Use correlation fields for joining with events

5. **Field Patterns:**
   - Universal infrastructure fields (k8s_*)
   - Application fields (level, message, logger_name)
   - Correlation fields (conversationId, turnId, correlationId)

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-31  
**Related Documents:** `event_field_relationships.md`, `logs_analysis.md`, `logs_broad_exploration.md`, `logs_system_prompt.md`

