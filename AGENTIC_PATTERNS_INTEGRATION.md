# Current architecture (single-shot)
Single LLM call for parsing
Schema discovery happens separately
Deterministic query building
Limited self-correction or refinement
1. ReAct (Reasoning + Acting)
Benefits for complex queries
Reasoning → Action loop:
Observation: User query mentions "events across multiple services"Thought: Need to understand schema across multiple indicesAction: Discover schema for each mentioned indexObservation: Field "response_status" exists in index A but not BThought: May need to use different fields or correlate dataAction: Refine query strategy
Implementation:
Multi-step query planning: break complex queries into sub-queries
Iterative schema exploration: discover schema incrementally based on query intent
Field mapping validation: validate discovered fields against query requirements
Example:
User: "Compare response times between legacy and supervisor variants across all services"→ ReAct Agent:  1. Think: Need to find fields related to response time, variant, service  2. Act: Query schema for fields matching "response", "time", "variant", "service"  3. Think: Found "responseTime", "variant" but need to join across indices  4. Act: Plan multi-index query strategy  5. Think: Validate all required fields exist  6. Act: Build composite query
2. AutoGen (Multi-Agent Collaboration)
Benefits for schema understanding and query decomposition
Specialized agents:
Schema Discovery Agent: explores and maps schema across indices
Query Planner Agent: decomposes complex queries into sub-queries
Field Validator Agent: validates field existence and types
Query Optimizer Agent: optimizes query performance
Coordinator Agent: orchestrates the conversation
Implementation:
or agent selection and outcomes"
  - Planner Agent: "Break into: 
User: "Get all events where user selected agent X but system used agent Y, with correlation to conversation outcomes"→ Coordinator Agent delegates:  - Schema Agent: "Find fields for agent selection and outcomes"  - Planner Agent: "Break into: 1) Find conversations, 2) Find agent selections, 3) Correlate"  - Validator Agent: "Validate 'selected-agent' and 'used-agent' fields exist"  - Optimizer Agent: "Plan efficient query order to minimize data scanning"
Useful when:
Complex multi-step queries need coordination
Schema spans multiple indices that need coordination
Queries require data correlation across different event types
3. DSPy (Declarative Prompt Engineering)
Benefits for query generation
Learnable prompts:
Optimize prompts based on query patterns
Improve schema-to-query mapping accuracy
Learn field name variations automatically
Implementation:
# DSPy Signature for query generationclass QueryGeneration(dspy.Signature):    """Generate OpenSearch query from natural language given schema"""    user_query: str = dspy.InputField()    schema_info: dict = dspy.InputField()    parsed_query: dict = dspy.OutputField()# Optimize prompts with examplesoptimizer = dspy.BootstrapFinetune(QueryGeneration)optimizer.compile(    train=[(query1, schema1, parsed1), (query2, schema2, parsed2)])
Useful for:
Improving parsing accuracy over time
Handling domain-specific query patterns
Learning field name synonyms (e.g., "response_time" vs "responseTime")
Adapting to user query styles
4. Reflection/Reflexion
Benefits for query validation and refinement
Self-correction loop:
1. Generate initial query2. Reflect: "Does this query capture all user requirements?"3. Validate against schema4. Reflect: "Are all fields valid? Are aggregations correct?"5. Refine query if needed6. Execute validation query (if possible)7. Reflect: "Would this return expected results?"
Implementation:
Validate query structure before building
Check field existence and types against schema
Verify query completeness (all requirements met?)
Self-correct field mapping errors
Suggest improvements for ambiguous queries
Example:
User: "Show completion rates by service"→ Generate: {"aggregations": [{"type": "count", "group_by": ["service"]}]}→ Reflect: "User said 'completion rates' - do they mean percentage or count?"→ Refine: Add percentage aggregation→ Reflect: "Is 'service' field name correct in schema?"→ Validate: Check schema - found "k8s_name" not "service"→ Final: Use correct field name
5. Planning (Chain-of-Thought Planning)
Benefits for multi-step query generation
Query decomposition:
User: "Find all conversations where user asked about X,        then show the agent responses and their outcomes,       grouped by service"Plan:Step 1: Discover schema for conversation indicesStep 2: Build query to find conversations with query content "X"Step 3: Extract conversation IDs from Step 2 resultsStep 4: Query agent response events using conversation IDsStep 5: Correlate outcomes from outcome eventsStep 6: Group final results by service
Implementation:
Break complex queries into sequential steps
Plan data dependencies (Step 2 needs Step 1 results)
Optimize execution order
Handle multi-index scenarios with proper joins/correlations
Useful for:
Queries requiring multiple data passes
Correlation analysis across event types
Progressive schema discovery based on intermediate results
Complex aggregations that need preliminary queries
6. Hierarchical Planning (for very complex queries)
Benefits for enterprise-scale queries
Multi-level planning:
Level 1: Overall strategy  "Need to correlate user queries, agent responses, and outcomes"Level 2: Sub-plans  Sub-plan A: Extract conversation data  Sub-plan B: Extract agent response data    Sub-plan C: Extract outcome data  Sub-plan D: Correlate using conversation IDsLevel 3: Query generation  For each sub-plan, generate specific OpenSearch queries
Useful when:
Queries span multiple data sources
Complex business logic requires multiple query stages
Schema discovery needs to be incremental (discover schema for Sub-plan A before planning Sub-plan B)
7. Self-RAG (Retrieval-Augmented Generation with Reflection)
Benefits for schema-aware query generation
Retrieve relevant schema → Generate → Reflect:
1. Retrieve: Find relevant schema fields based on query keywords2. Generate: Create query using retrieved schema3. Reflect: "Are all referenced fields in the retrieved schema?"4. Retrieve: If missing fields, retrieve more schema info5. Generate: Update query with complete schema
Implementation:
Semantic search through schema descriptions
Retrieve only relevant fields (not entire schema)
Iteratively refine schema retrieval based on query requirements
Example:
User: "Find slow API calls"→ Retrieve: Fields matching "api", "call", "time", "duration", "latency"→ Generate: Query using retrieved fields→ Reflect: "Is 'slow' adequately captured?"→ Retrieve: Additional time-related fields if needed
Recommended hybrid approach for NLAP
Combine patterns for a robust system:
┌─────────────────────────────────────────┐│  User Input                              │└──────────────┬──────────────────────────┘               │               ▼┌─────────────────────────────────────────┐│  ReAct Planner Agent                     ││  - Plans high-level strategy             ││  - Determines which indices needed       │└──────────────┬──────────────────────────┘               │               ▼┌─────────────────────────────────────────┐│  Self-RAG Schema Discovery               ││  - Retrieves relevant schema fields      ││  - Iterates until all fields found       │└──────────────┬──────────────────────────┘               │               ▼┌─────────────────────────────────────────┐│  Reflection Query Generator              ││  - Generates initial query               ││  - Reflects: validates against schema    ││  - Refines: corrects field mappings      │└──────────────┬──────────────────────────┘               │               ▼┌─────────────────────────────────────────┐│  DSPy Optimized Query Builder            ││  - Uses learned patterns                 ││  - Optimizes query structure             │└──────────────┬──────────────────────────┘               │               ▼┌─────────────────────────────────────────┐│  Final OpenSearch Query                  │└─────────────────────────────────────────┘
Specific improvements for complex queries
Multi-index queries: Use AutoGen for coordination across indices
Correlation queries: Use Planning to break into sequential steps
Schema mismatches: Use Reflection to detect and fix field mapping issues
Ambiguous queries: Use ReAct to ask clarifying questions or infer intent
Performance: Use Planning to optimize query execution order
Implementation priority
Phase 1: Add Reflection — immediate validation and self-correction
Phase 2: Add Planning — handle multi-step complex queries
Phase 3: Add ReAct — enable iterative refinement
Phase 4: Add AutoGen — for enterprise-scale multi-agent coordination
Phase 5: Add DSPy — for continuous learning and optimization
This transforms the system from single-shot to adaptive, self-correcting, and capable of handling complex multi-step queries with proper schema understanding.