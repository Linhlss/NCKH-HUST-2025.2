from __future__ import annotations

import uvicorn

from project_root.api import app


if __name__ == "__main__":
    uvicorn.run("project_root.api:app", host="0.0.0.0", port=8000, reload=False)
