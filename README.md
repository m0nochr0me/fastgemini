# FastGemini

A FastAPI-style framework for building Gemini protocol servers in Python.

## Features

- 🚀 **FastAPI-style decorators** - Define routes with familiar `@app.route()` syntax
- 📦 **Router support** - Organize routes with `GeminiRouter` (like APIRouter)
- 🔧 **Path parameters** - Extract values from URLs: `/user/{username}`
- ⚡  **Async/await** - Built on Trio for high-performance async I/O
- 🛡️ **TLS/SSL** - Native client certificate support
- 🎯 **Type hints** - Full Pydantic integration for request/response models

## Installation

```bash
pip install fastgemini
```

## Quick Start

```python
from fastgemini import GeminiApp, success
from fastgemini.schema import GeminiRequest, GeminiResponse

app = GeminiApp(
    certfile="path/to/cert.cer",
    keyfile="path/to/key.key",
)

@app.route("/")
async def index(request: GeminiRequest) -> GeminiResponse:
    return success("# Welcome to Gemini!\n")

@app.route("/hello/{name}")
async def hello(request: GeminiRequest) -> GeminiResponse:
    name = request.path_params["name"]
    return success(f"# Hello, {name}!\n")

if __name__ == "__main__":
    app.run()
```

## Using Routers

```python
from fastgemini import GeminiApp, GeminiRouter, success

app = GeminiApp(
    certfile="path/to/cert.cer",
    keyfile="path/to/key.key",
)
users = GeminiRouter(prefix="/users")

@users.route("/")
async def list_users(request):
    return success("# Users\n=> /users/alice Alice\n")

@users.route("/{username}")
async def get_user(request):
    return success(f"# User: {request.path_params['username']}\n")

app.include_router(users)
```

## Response Helpers

```python
from fastgemini import success, redirect, not_found, input_required, error

# Success with body
success("# Hello World\n")

# Redirects
redirect("/new-location")
redirect("/permanent", permanent=True)

# Errors
not_found("Page not found")
error("Something went wrong")

# Input prompts
input_required("Enter your name:")
input_required("Enter password:", sensitive=True)
```

