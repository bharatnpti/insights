# IntelliJ IDEA Debugging Setup Guide

This guide explains how to set up debugging in IntelliJ IDEA for this FastAPI application using the existing `.venv` and `uv` environment.

## Prerequisites

- IntelliJ IDEA (with Python plugin installed)
- Project opened in IntelliJ IDEA
- `.venv` virtual environment exists (already set up with `uv`)

## Step-by-Step Setup

### 1. Configure Python Interpreter

1. Open **File** → **Settings** (or **IntelliJ IDEA** → **Preferences** on macOS)
2. Navigate to **Project: insights** → **Python Interpreter**
3. Click the gear icon ⚙️ → **Add...**
4. Select **Existing environment**
5. Choose the interpreter: `$PROJECT_DIR$/.venv/bin/python3`
   - Or browse to: `/Users/bharatbhushan/IdeaProjects/bharatnpti/insights/.venv/bin/python3`
6. Click **OK** to save

### 2. Mark Source Directories

1. Right-click on the `src` folder in the project tree
2. Select **Mark Directory as** → **Sources Root**
3. This ensures IntelliJ can find your `nlap` module

### 3. Use Pre-configured Run Configuration

Three run configurations have been created:

#### Option A: FastAPI Debug (Module Mode) - **RECOMMENDED FOR DEBUGGING**
- Uses: Python module mode with uvicorn from `.venv`
- Command: `uvicorn nlap.main:app --reload --host 0.0.0.0 --port 8000`
- Best for debugging as it properly handles breakpoints

#### Option B: FastAPI Debug (direct uvicorn)
- Uses: `.venv/bin/uvicorn` directly
- Command: `nlap.main:app --reload --host 0.0.0.0 --port 8000`

#### Option C: FastAPI Debug (with uv)
- Uses: `uv run` command (respects uv environment)
- Command: `uv run uvicorn nlap.main:app --reload --host 0.0.0.0 --port 8000`

### 4. Start Debugging

1. Open the run configuration dropdown (top toolbar)
2. Select **"FastAPI Debug (Module Mode)"** (recommended) or any other configuration
3. Click the debug icon (🐛) next to the run configuration
   - Or press `Shift + F9` (Windows/Linux) or `Ctrl + Shift + D` (macOS)
4. The application will start in debug mode

### 5. Set Breakpoints

1. Open any Python file (e.g., `src/nlap/main.py`, `src/nlap/api/routes/query.py`)
2. Click in the left gutter (line numbers area) to set a breakpoint
   - A red dot appears indicating the breakpoint
3. When the code execution reaches that line, IntelliJ will pause

### 6. Debug Controls

Once stopped at a breakpoint:
- **F8** (Step Over): Execute current line, move to next
- **F7** (Step Into): Step into function calls
- **Shift + F8** (Step Out): Step out of current function
- **F9** (Resume): Continue execution until next breakpoint
- **Ctrl + F8** (Toggle Breakpoint): Add/remove breakpoint

### 7. Inspect Variables

When paused at a breakpoint:
- View variables in the **Variables** panel (bottom)
- Use **Evaluate Expression** (Alt + F8) to run code expressions
- Hover over variables in the editor to see their values

## Manual Configuration (Alternative)

If the pre-configured run configurations don't work, create a new one:

1. **Run** → **Edit Configurations...**
2. Click **+** → **Python**
3. Configure:
   - **Name**: FastAPI Debug
   - **Script path**: `.venv/bin/uvicorn`
   - **Parameters**: `nlap.main:app --reload --host 0.0.0.0 --port 8000`
   - **Python interpreter**: `.venv/bin/python3`
   - **Working directory**: Project root
   - **Environment variables**: `PYTHONUNBUFFERED=1`
4. Click **OK**

## Troubleshooting

### Interpreter not found
- Ensure `.venv` exists: `ls -la .venv`
- In IntelliJ: **File** → **Settings** → **Project: insights** → **Python Interpreter**
- Click the gear icon → **Add...** → **Existing environment**
- Select: `$PROJECT_DIR$/.venv/bin/python3`
- Recreate if needed: `uv sync`

### Breakpoints not hit
- Ensure you're running in **Debug mode** (🐛 icon), not Run mode (▶️)
- Check that the interpreter matches the `.venv` interpreter
- Verify source roots are marked correctly

### Module not found errors
- Right-click `src` → **Mark Directory as** → **Sources Root**
- Invalidate caches: **File** → **Invalidate Caches...** → **Invalidate and Restart**

### Port already in use
- Change port in run configuration parameters: `--port 8001`
- Or stop the existing process using port 8000

## Testing the Setup

1. Set a breakpoint in `src/nlap/main.py` at line 24 (inside `lifespan` function)
2. Start debugging
3. The application should pause at the breakpoint
4. You should see variables and can inspect the application state

## Additional Tips

- **Conditional Breakpoints**: Right-click a breakpoint → **More** → Add condition
- **Logpoints**: Right-click gutter → **Add Logpoint** (prints without stopping)
- **Remote Debugging**: For debugging deployed applications, use the PyCharm/IntelliJ remote debugger

