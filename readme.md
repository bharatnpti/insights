# Natural Language Analytics Platform (NLAP)

A comprehensive platform that allows users to input natural language requirements and automatically extract, analyze, and visualize data from OpenSearch indices with CSV output generation.

## Overview

The Natural Language Analytics Platform (NLAP) is designed to bridge the gap between natural language queries and complex OpenSearch data extraction. It leverages Azure OpenAI to understand user intent and automatically generates optimized OpenSearch queries.

## Architecture

The platform follows a modular architecture:

```
src/nlap/
├── config/          # Configuration management (Pydantic Settings)
├── opensearch/      # OpenSearch client and query management
├── azureopenai/     # Azure OpenAI client with Azure AD authentication
├── api/             # FastAPI REST API layer
│   └── routes/      # API route handlers
├── models/          # Shared Pydantic data models
└── utils/           # Utility modules (logging, etc.)
```

## Features

- **Natural Language Processing**: Parse and understand user queries using Azure OpenAI
- **OpenSearch Integration**: Direct connection to OpenSearch clusters with basic authentication
- **Structured Logging**: Production-grade JSON logging compatible with OpenSearch
- **Health Monitoring**: Comprehensive health check endpoints
- **Async/Await Support**: Full asynchronous I/O for optimal performance
- **Type Safety**: Built with Pydantic for robust data validation

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Access to OpenSearch cluster
- Azure subscription with OpenAI service and appropriate Azure AD credentials

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd insights
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

5. **Configure environment variables** in `.env`:
   - Set your OpenSearch connection details
   - Configure Azure OpenAI endpoint and deployment name
   - Adjust application settings as needed

## Configuration

### Environment Variables

The application uses environment variables for configuration. See `.env.example` for all available options.

#### Required Variables

- `OPENSEARCH_HOST`: OpenSearch cluster endpoint
- `OPENSEARCH_USERNAME`: Basic auth username
- `OPENSEARCH_PASSWORD`: Basic auth password
- `AZURE_ENDPOINT`: Azure OpenAI endpoint URL

#### Optional Variables

- `OPENSEARCH_PORT`: OpenSearch port (default: 9200)
- `OPENSEARCH_USE_SSL`: Enable SSL (default: true)
- `AZURE_DEPLOYMENT_NAME`: Model deployment name (default: gpt-4)
- `AZURE_API_VERSION`: API version (default: 2024-10-21)
- `LOG_LEVEL`: Logging level (default: INFO)

### Azure AD Authentication

The application uses `DefaultAzureCredential` for Azure AD authentication. Ensure you have appropriate Azure credentials configured:

- Azure CLI: `az login`
- Environment variables: `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
- Managed Identity (when running on Azure)

## Usage

### Running the Application

Start the FastAPI server:

```bash
uv run uvicorn nlap.main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python directly:

```bash
uv run python -m uvicorn nlap.main:app --reload
```

### API Documentation

Once running, access the interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Health Check

Check application health:

```bash
curl http://localhost:8000/health
```

## Development

### Project Structure

- `src/nlap/`: Main application package
- `tests/`: Test suite
- `pyproject.toml`: Project configuration and dependencies

### Running Tests

Run all tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=src --cov-report=html
```

#### Testing Azure OpenAI Client

The test suite includes comprehensive tests for Azure OpenAI client with multiple deployments across different regions. To run Azure OpenAI tests, ensure you have Azure AD credentials configured (see Azure AD Authentication section above).

**Quick test with a specific deployment:**

```bash
# Test with GPT4-UK
export AZURE_ENDPOINT='https://gpt4-uk.openai.azure.com/'
export AZURE_DEPLOYMENT_NAME='GPT4-UK'
export AZURE_API_VERSION='2024-10-21'
uv run pytest tests/unit/test_azure_openai_client.py -v
```

**Manual testing script:**

For quick manual testing without the full test suite:

```bash
# Test single deployment
export AZURE_ENDPOINT='https://gpt4-uk.openai.azure.com/'
export AZURE_DEPLOYMENT_NAME='GPT4-UK'
export AZURE_API_VERSION='2024-10-21'
python test_azure_openai_manual.py

# Test all quick configurations
python test_azure_openai_manual.py --all
```

**Available test configurations:**

The test suite includes configurations for:
- **GPT4-UK** (UK South): `GPT4-UK`, `GPT4-32k-UK`, `GPT35T0301`, `GPT35T-1106`
- **GPT4-SE-dev** (Sweden Central): `GPT-4o`, `GPT4-turbo`, `gpt-4o-mini-real`, `dt-gpt-35-turbo-16k`
- **gpt-us-testenv** (East US): `gpt4-0125-us`, `gpt-35-t-0301`, `gpt-4o-mini`

See the test file `tests/unit/test_azure_openai_client.py` for all available configurations.

### Code Quality

Format code with Black:

```bash
uv run black src tests
```

Lint with Ruff:

```bash
uv run ruff check src tests
```

Type checking with mypy:

```bash
uv run mypy src
```

## Logging

The application uses `structlog` for structured logging with JSON output in production. Logs are formatted to be compatible with OpenSearch ingestion.

### Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### Context Variables

The logging system supports context variables for distributed tracing:

- `request_id`: Unique request identifier
- `user_id`: User identifier (when available)
- `correlation_id`: Correlation identifier

## API Endpoints

### Health Check

- `GET /health`: Comprehensive health check
- `GET /health/readiness`: Readiness probe
- `GET /health/liveness`: Liveness probe

More endpoints will be added as development progresses.

## Technology Stack

- **Python 3.12+**: Modern Python with latest features
- **FastAPI**: High-performance async web framework
- **uv**: Fast Python package manager
- **OpenSearch Python Client**: Official OpenSearch client
- **Azure OpenAI**: Azure OpenAI service integration
- **Pydantic**: Data validation using Python type annotations
- **structlog**: Structured logging framework

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and ensure code quality checks pass
4. Submit a pull request

## License

MIT

## Roadmap

See `jiras.md` for detailed project roadmap and feature list.

## Support

For issues and questions, please open an issue in the repository.
