from typing import Any

from fastapi.responses import JSONResponse


class JSONLDResponse(JSONResponse):
    """JSON-LD response class for structured data"""

    def __init__(self, content: Any = None, **kwargs: Any) -> None:
        if content is None:
            content = {}

        # Add JSON-LD context if not present
        if isinstance(content, dict) and "@context" not in content:
            content["@context"] = "https://www.w3.org/ns/hydra/context.jsonld"

        super().__init__(content=content, **kwargs)
