#!/usr/bin/env python3
"""
Wrapper script to run uvicorn for IntelliJ debugging.

This script runs uvicorn directly using the venv's uvicorn installation.
Since the venv is managed by uv, all dependencies are already correctly installed.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "nlap.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

