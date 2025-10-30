# OpenSearch Logs Broad Exploration Analysis

**Generated:** 2025-10-31  
**Index:** `ia-platform-prod-*`  
**Date Range:** 2025-10-27 to 2025-10-30  
**Analysis Type:** Comprehensive Broad Exploration - Field Relationships, Patterns, and System Behavior

---

## Executive Summary

This analysis extends the field discovery with a broader exploration of:
- Field co-occurrence patterns
- Event sequences and flows
- Performance metrics and patterns
- Error and exception handling
- Service interactions
- User interaction patterns
- Agent behavior patterns
- Function call patterns
- Intent detection patterns
- LLM usage patterns

---

## Field Co-Occurrence Analysis

### Critical Findings

**Fields that NEVER appear together (require correlation):**
- `ab_experiment_variant` + `response_status`: **0 documents** (0%)
  - **Action Required:** Must correlate using conversationId + turnId
- `ab_experiment_variant` + `markedForAgentHandover`: **0 documents** (0%)
- `ab_experiment_variant` + `markedResolved`: **0 documents** (0%)
- `response_status` + `markedForAgentHandover`: **0 documents** (0%)
- `response_status` + `markedResolved`: **0 documents** (0%)
- `markedForAgentHandover` + `markedResolved`: **0 documents** (0%)

**Fields that ALWAYS appear together (can query together):**
- `conversationId` + `turnId`: **10,000 documents** (100%)
- `conversationId` + `event`: **10,000 documents** (100%)
- `ab_experiment_variant` + `conversationId`: **10,000 documents** (100%)
- `response_status` + `conversationId`: **10,000 documents** (100%)

### Implications

1. **A/B Test to Completion Status Correlation:**
   - Cannot use single query with both fields
   - **Strategy:** Query separately and join on `conversationId` + `turnId`
   - Expected correlation rate: ~6-7% based on previous analysis

2. **Completion Status Fields:**
   - `response_status` is in different events than `markedForAgentHandover`/`markedResolved`
   - Use `response_status` as primary indicator (from RESPONSE_RETURNED events)
   - Use `markedForAgentHandover` from AGENT_HANDOVER_DETECTION_COMPLETED events

3. **Reliable Correlation Keys:**
   - `conversationId` + `turnId` combination appears in most events
   - Always query both fields when correlating data

---

## Performance Metrics Analysis

### Duration Metrics

**Field:** `duration`
- **Type:** Numeric (milliseconds)
- **Count:** 5,041,964 occurrences
- **Statistics:**
  - Min: 0.0 ms
  - Max: 228,668,215.0 ms (~2.6 days)
  - Average: 21,112.64 ms (~21 seconds)
  - **Percentiles:**
    - P50 (median): 14.0 ms
    - P75: 71.59 ms
    - P90: 1,163.65 ms (~1.2 seconds)
    - P95: 1,547.57 ms (~1.5 seconds)
    - P99: 124,923.43 ms (~2.1 minutes)

**Key Insight:** Most requests are fast (median 14ms), but tail latency can be very high.

### Response Time Fields

**Field:** `responseTime`
- **Type:** String (e.g., "1.043574428s")
- **Format:** Duration in seconds with 's' suffix
- **Top Values:** Various response times between 1-2 seconds

**Field:** `responseTimeInMs`
- **Type:** String (e.g., "272")
- **Format:** Milliseconds as string
- **Top Values:**
  - "272": 786 occurrences
  - "274": 760 occurrences
  - "268": 746 occurrences
  - "261": 741 occurrences

**Field:** `upstream_service_time`
- **Type:** String
- **Usage:** Service response time tracking

### Token Usage Metrics

**Field:** `totalTokens`
- **Type:** String
- **Top Values:**
  - "239": 2,348 occurrences
  - "838": 2,302 occurrences
  - "231": 2,026 occurrences

**Field:** `completionTokens`
- **Type:** String
- **Top Values:**
  - "39": 91,989 occurrences (most common)
  - "11": 58,793 occurrences
  - "3": 32,126 occurrences
  - "4": 23,580 occurrences

**Field:** `promptTokens`
- **Type:** String
- **Top Values:**
  - "228": 2,329 occurrences
  - "835": 2,326 occurrences
  - "229": 2,237 occurrences

**Usage Pattern:** Token counts stored as strings, need to convert to numeric for calculations.

---

## Error Patterns Analysis

### Error-Related Fields Discovered

**3 error-related fields found:**

1. **`function_error_message`**
   - Contains error messages from function calls
   - Appears in FUNCTION_CALL_COMPLETED events
   - **Usage:** Track what went wrong in function calls

2. **`error`** (general error field)
   - Generic error information
   - **Usage:** General error tracking

3. **`errorType`** (if exists)
   - Error categorization
   - **Usage:** Error type classification

### Error Detection Strategy

When user queries about errors:
1. Look for `function_error_message` in FUNCTION_CALL_COMPLETED events
2. Check `function_status` field for "error" values
3. Search for `error` field in various events
4. Check log levels (level=ERROR)

---

## Service Interactions Analysis

### Top Services by Event Count

| Service | Event Count | Event Types | Containers |
|---------|-------------|-------------|------------|
| **ia-platform** | 14,608,025 | 10 types | ia-platform |
| **anonymization-service** | 4,019,699 | 0 (proxy logs) | anonymization-service, istio-proxy |
| **search-service** | 1,646,335 | 0 (proxy logs) | istio-proxy |
| **contract-agent-service** | 474,210 | 7 types | contract-agent-service |
| **flexcard-agent-service** | 423,222 | 3 types | flexcard-agent-service |
| **invoice-agent-service** | 361,707 | 5 types | invoice-agent-service |
| **oneai-chat-bff** | 326,406 | 0 (proxy logs) | istio-proxy |
| **ivr-billing-agent-service** | 242,128 | 7 types | ivr-billing-agent-service |
| **order-agent-service** | 226,402 | 5 types | order-agent-service |
| **sim-agent-service** | 204,927 | 5 types | sim-agent-service |

### Service Patterns

1. **Main Platform (ia-platform):**
   - Highest event count
   - Most diverse event types (10 different types)
   - Core conversation processing

2. **Agent Services:**
   - Specialized services for different domains
   - Each has 3-7 event types
   - Examples: contract, flexcard, invoice, billing, order, sim

3. **Supporting Services:**
   - anonymization-service: High volume (message processing)
   - search-service: Search operations
   - oneai-chat-bff: Backend for frontend

4. **Proxy Logs:**
   - Many services show 0 event types but high counts
   - These are istio-proxy access logs
   - Contains HTTP request/response data

---

## User Interaction Patterns

### Channel Analysis

**Field:** `channelId`
- **7 unique values found**
- **Top Channels:**
  - ONEAPP (mobile app)
  - WEB (web interface)
  - IVR (Interactive Voice Response)
  - Various other channels

**Query Pattern:**
```json
{"terms": {"channelId": ["ONEAPP", "WEB", "IVR"]}}
```

### Intent Patterns

**Field:** `source_intent`
- **20-30 unique values** (varies by query)
- **Usage:** Original intent from NLU
- **Top Intents:** (German intent names)
  - Various customer service intents

**Field:** `detectedIntent`
- **7 unique values**
- **Usage:** Detected intent after processing
- **Pattern:** More aggregated than source_intent

**Field:** `explicitIntent`
- **1 unique value** (mostly empty/null)
- **Usage:** User explicitly stated intent

**Field:** `category`
- **30 unique values**
- **Usage:** Intent category classification
- **Pattern:** Hierarchical intent structure

**Field:** `subCategory`
- **30 unique values**
- **Usage:** Intent subcategory
- **Pattern:** More granular than category

### Language Model Usage

**Field:** `languageModel`
- **8 unique values**
- **Top Models:**
  - GPT-4o-mini (most common)
  - GPT-4
  - Other model variants

**Query Pattern:**
```json
{"terms": {"languageModel": ["GPT-4o-mini", "GPT-4"]}}
```

### Tenant Analysis

**Field:** `tenant`
- **5 unique values**
- **Usage:** Multi-tenant support
- **Values:** "de" (Germany), and others
- **Pattern:** Mostly "de" tenant

---

## Agent Patterns Analysis

### Agents Discovered

**30 unique agents found**

**Agent Fields:**
- `agent`: General agent identifier
- `classifier-selected-agent`: Agent selected by classifier
- `callingAgent`: Agent that called a function

### Agent Selection Patterns

**Field:** `classifier-selected-agent`
- **17 unique agents** selected by classifier
- **Usage:** ML-based agent routing
- **Events:** CLASSIFICATION_VECTOR_DONE, CLASSIFICATION_LLM_DONE, CLASSIFICATION_FASTTRACK_DONE

**Agent Types:**
- Domain-specific agents (contract, invoice, billing, etc.)
- Generic agents (LmosAgent)
- Specialized agents for specific use cases

### Agent Correlation

**Agent appears with:**
- `step`: Processing steps
- `source_intent`: User intents
- `vaspConnId`: VASP connection
- `languageModel`: LLM model used

---

## Function Call Patterns

### Functions Discovered

**30 unique functions analyzed**

**Function Fields:**
- `function`: Function name
- `function_status`: Execution status
- `function_input`: Input parameters
- `function_output`: Output data
- `function_error_message`: Error information (if any)
- `phase`: Function execution phase (Generating, FilterOutput, generatePrompt, FilterInput)

### Function Status Distribution

**Status Values:**
- success: Successful execution
- error: Function failed
- Other status values

### Function Phases

**Field:** `phase`
- **4 unique values:**
  1. **Generating**: 830,566 occurrences (43.1%)
  2. **FilterOutput**: 736,964 occurrences (38.2%)
  3. **generatePrompt**: 289,616 occurrences (15.0%)
  4. **FilterInput**: 70,296 occurrences (3.6%)

**Pattern:** Shows function execution lifecycle from input filtering → prompt generation → response generation → output filtering

### Function Correlation

Functions appear with:
- `conversationId`, `turnId`: Conversation context
- `agent`: Calling agent
- `variant`: Feature variant
- `input`: Function input data

---

## Intent Detection Patterns

### Intent Fields Hierarchy

**Intent Detection Flow:**
1. `source_intent`: Initial NLU intent
2. `detectedIntent`: Processed/detected intent
3. `explicitIntent`: User-stated intent
4. `category`: Intent category
5. `subCategory`: Intent subcategory

### Intent Value Analysis

**source_intent:**
- **30 unique values**
- Most diverse field
- Raw NLU output

**detectedIntent:**
- **7 unique values**
- More aggregated
- Processed intent

**explicitIntent:**
- **1 unique value** (mostly empty)
- User explicitly stated

**category & subCategory:**
- **30 unique values each**
- Hierarchical classification
- Used for routing and analysis

### Intent Events

**Key Events:**
- `INTENT_DETECTION_COMPLETED`: Intent detection finished
- `INTENT_TRAFFIC_SPLIT`: Intent routing decision
- `USECASE_PROMPT_IDENTIFIED`: Use case determined from intent

---

## Event Sequences Analysis

### Typical Conversation Flow

Based on analyzed sequences, typical event order:

1. **RECEIVED_CHAT_MESSAGE** - User message received
2. **CHAT_REQUEST_PROCESSING_STARTED** - Processing begins
3. **TRANSCRIPT_PREPARED** - Transcript ready
4. **USECASE_PROMPT_IDENTIFIED** - Use case determined
5. **INTENT_DETECTION_COMPLETED** - Intent identified
6. **INTENT_TRAFFIC_SPLIT** - Routing decision made
7. **CLASSIFICATION_*_DONE** - Agent classification completed
8. **LLM_STARTED** - LLM processing begins
9. **FUNCTION_CALLED** (multiple) - Functions executed
10. **LLM_COMPLETED** - LLM processing done
11. **RESPONSE_GENERATION_COMPLETED** - Response generated
12. **RESPONSE_RETURNED** - Response returned (with response_status)

### Sequence Variations

- Not all conversations follow exact same sequence
- Some steps may be skipped
- Parallel processing possible (multiple function calls)
- Some events may occur out of order

---

## LLM Usage Patterns

### Model Distribution

**Field:** `languageModel`
- Primary field for LLM tracking
- **8 unique models** found
- **Most common:** GPT-4o-mini

### Token Usage Patterns

**Completion Tokens:**
- Most common: 39 tokens (91,989 occurrences)
- Typical range: 3-40 tokens
- Patterns suggest:
  - Short responses: 3-11 tokens
  - Medium responses: 39 tokens
  - Long responses: Varied

**Prompt Tokens:**
- Typical: 200-835 tokens
- Suggests context-rich prompts

**Total Token Ranges:**
- Small: 200-250 tokens
- Large: 800+ tokens

### LLM Events

**Key Events:**
- `LLM_STARTED`: LLM processing begins
- `LLM_COMPLETED`: LLM processing completes (with token counts)

**Correlation:**
- Appears with `step`, `languageModel`, `prompt`, `messages`
- Token metrics available in LLM_COMPLETED events

---

## Query Building Implications

### Correlation Requirements

Based on co-occurrence analysis:

**Must correlate (different events):**
- A/B test variant + completion status
- A/B test variant + handover status
- Completion status + marked flags

**Correlation Strategy:**
```python
# Query 1: A/B test events
ab_query = {"query": {"bool": {"must": [{"exists": {"field": "ab_experiment_variant"}}]}}}

# Query 2: Completion events  
completion_query = {"query": {"bool": {"must": [{"exists": {"field": "response_status"}}]}}}

# Join in application
merged = ab_df.merge(completion_df, on=['conversationId', 'turnId'], how='left')
```

### Field Format Handling

**Always check both formats:**
- camelCase: `conversationId`, `turnId`, `traceId`
- snake_case: `conversation_id`, `turn_id`, `trace_id`

**Query Pattern:**
```json
{
  "bool": {
    "should": [
      {"term": {"conversationId": "<id>"}},
      {"term": {"conversation_id": "<id>"}}
    ]
  }
}
```

### Performance Field Handling

**Token fields are strings:**
- Need to convert to numeric for calculations
- Pattern: `int(totalTokens)` or `int(completionTokens)`

**Duration fields:**
- `duration`: Already numeric (milliseconds)
- `responseTime`: String format (e.g., "1.043s")
- `responseTimeInMs`: String format (e.g., "272")

---

## Service-Level Analysis Patterns

### Service Querying

**Query by service:**
```json
{
  "term": {"k8s_name": "ia-platform"}
}
```

**Query by container:**
```json
{
  "term": {"k8s_container": "ia-platform"}
}
```

**Query by pod:**
```json
{
  "term": {"k8s_pod": "ia-platform-74c6dc676c-btgtt"}
}
```

### Service Event Types

**Services with application events:**
- ia-platform: 10 event types
- contract-agent-service: 7 event types
- ivr-billing-agent-service: 7 event types
- invoice-agent-service: 5 event types
- order-agent-service: 5 event types
- sim-agent-service: 5 event types
- flexcard-agent-service: 3 event types

**Services with only proxy logs:**
- anonymization-service
- search-service
- oneai-chat-bff

---

## Agent Analysis Patterns

### Querying Agent Data

**Find agent selection:**
```json
{
  "exists": {"field": "classifier-selected-agent"}
}
```

**Find agent usage:**
```json
{
  "term": {"agent": "LmosAgent"}
}
```

**Find agent context:**
```json
{
  "term": {"callingAgent": "<agent-name>"}
}
```

### Agent Correlation

Agents correlate with:
- `step`: Processing steps
- `source_intent`: User intents
- `languageModel`: LLM models used
- `function`: Functions called

---

## Intent Analysis Patterns

### Intent Detection Flow

1. **User Input** → `source_intent` (raw NLU)
2. **Processing** → `detectedIntent` (processed)
3. **Classification** → `category` + `subCategory`
4. **Routing** → Agent selection based on intent

### Intent Query Patterns

**Query by intent:**
```json
{
  "term": {"source_intent": "rechnung"}
}
```

**Query by category:**
```json
{
  "term": {"category": "<category>"}
}
```

**Query intent traffic split:**
```json
{
  "term": {"event": "INTENT_TRAFFIC_SPLIT"}
}
```

---

## Function Call Analysis Patterns

### Function Execution Lifecycle

**Phases:**
1. **FilterInput** (70K occurrences) - Filter input data
2. **generatePrompt** (290K occurrences) - Generate LLM prompt
3. **Generating** (831K occurrences) - Execute LLM call
4. **FilterOutput** (737K occurrences) - Filter output data

### Function Status Tracking

**Query successful functions:**
```json
{
  "term": {"function_status": "success"}
}
```

**Query failed functions:**
```json
{
  "term": {"function_status": "error"}
}
```

**Query function errors:**
```json
{
  "exists": {"field": "function_error_message"}
}
```

---

## Recommendations for Generic NL Processing

### 1. Field Correlation Matrix

**Create mapping:**
```python
CORRELATION_STRATEGY = {
    ("ab_experiment_variant", "response_status"): {
        "method": "join",
        "keys": ["conversationId", "turnId"],
        "expected_rate": 0.067  # 6.7%
    },
    ("ab_experiment_variant", "markedForAgentHandover"): {
        "method": "join",
        "keys": ["conversationId", "turnId"],
        "event_types": ["AB_EXPERIMENT_RETRIEVED", "AGENT_HANDOVER_DETECTION_COMPLETED"]
    }
}
```

### 2. Performance Metric Extraction

**Token fields:**
- Always convert string to int for calculations
- Handle missing values
- Aggregate: sum, avg, p95, p99

**Duration fields:**
- `duration` is numeric (already in ms)
- `responseTime` needs parsing (string format)
- Calculate percentiles for performance analysis

### 3. Service-Level Queries

**When user mentions:**
- "service performance" → Query by `k8s_name`
- "container logs" → Query by `k8s_container`
- "pod issues" → Query by `k8s_pod`

### 4. Intent Analysis Queries

**When user mentions:**
- "intent distribution" → Aggregate by `source_intent` or `detectedIntent`
- "intent categories" → Aggregate by `category`, `subCategory`
- "intent routing" → Query `INTENT_TRAFFIC_SPLIT` events

### 5. Agent Analysis Queries

**When user mentions:**
- "agent selection" → Query `classifier-selected-agent` field
- "agent performance" → Query by `agent` field
- "agent routing" → Analyze CLASSIFICATION_*_DONE events

---

## Data Quality Insights

### Co-occurrence Insights

1. **A/B test and completion status are in different events**
   - Correlation requires joining
   - Only ~6-7% correlation rate
   - Use conversationId + turnId for joining

2. **markedForAgentHandover and markedResolved don't appear together**
   - They're in different event types
   - Use response_status as primary completion indicator

3. **conversationId and turnId always appear together**
   - Reliable correlation key
   - Use for joining datasets

### Performance Data Quality

- Token counts stored as strings (need conversion)
- Duration is numeric (good for calculations)
- Response times in mixed formats (string and numeric)

### Event Sequence Quality

- Sequences can vary
- Some events may be missing
- Parallel processing creates non-linear sequences

---

## Complete Field Reference

### Performance Fields
- `duration` (numeric, ms)
- `responseTime` (string, seconds format)
- `responseTimeInMs` (string, milliseconds)
- `upstream_service_time` (string)
- `totalTokens` (string, needs conversion)
- `completionTokens` (string, needs conversion)
- `promptTokens` (string, needs conversion)

### Error Fields
- `function_error_message` (string)
- `error` (string)
- `errorType` (string, if exists)
- `function_status` (can indicate errors)

### Intent Fields
- `source_intent` (raw NLU intent)
- `detectedIntent` (processed intent)
- `explicitIntent` (user-stated intent)
- `category` (intent category)
- `subCategory` (intent subcategory)

### Agent Fields
- `agent` (general agent)
- `classifier-selected-agent` (ML-selected agent)
- `callingAgent` (agent calling function)

### Function Fields
- `function` (function name)
- `function_status` (success/error)
- `function_input` (input data)
- `function_output` (output data)
- `function_error_message` (error info)
- `phase` (execution phase)

### Service Fields
- `k8s_name` (service name)
- `k8s_container` (container name)
- `k8s_pod` (pod name)
- `k8s_host` (host machine)
- `cicd` (CI/CD service)
- `cicd-pipeline` (pipeline ID)

---

## Usage Examples

### Example: Performance Analysis

**Query:** "Show average response time by variant"

**Processing:**
1. Query A/B test events (get variants)
2. Query LLM_COMPLETED events (get responseTime)
3. Join on conversationId + turnId
4. Calculate average responseTime by variant
5. Convert string to numeric if needed

### Example: Intent Analysis

**Query:** "Show intent distribution by agent"

**Processing:**
1. Query CLASSIFICATION_*_DONE events
2. Aggregate by `classifier-selected-agent` and `source_intent`
3. Create cross-tabulation
4. Calculate percentages

### Example: Function Call Analysis

**Query:** "Show function error rates by phase"

**Processing:**
1. Query FUNCTION_CALL_COMPLETED events
2. Filter by `function_status=error`
3. Group by `phase`
4. Calculate error rates

---

## Key Takeaways

1. **Correlation is Required:**
   - Most interesting fields don't appear together
   - Always use conversationId + turnId for correlation
   - Expect correlation rates of 6-10% typically

2. **Field Format Variations:**
   - Check both camelCase and snake_case
   - Token/duration fields may be strings or numbers
   - Always verify field types before aggregating

3. **Event Types Matter:**
   - Different fields appear in different events
   - Filter by event type to find relevant documents
   - Use event sequences to understand flows

4. **Service Structure:**
   - Main platform (ia-platform) handles most events
   - Specialized agent services for domains
   - Proxy logs provide infrastructure metrics

5. **Performance Patterns:**
   - Most requests are fast (median 14ms)
   - Tail latency can be very high (p99: ~2 minutes)
   - Token usage patterns show common response sizes

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-31  
**Related Documents:** `logs_analysis.md`, `logs_system_prompt.md`, `field_documentation.json`
