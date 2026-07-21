from fastapi import FastAPI

from app.api.v1.health.health_controller import health_router
from app.api.v1.router import api_router
from app.core.config import get_project_version, settings
from app.core.lifespan import lifespan
from app.core.logging_setup import setup_logging
from app.core.middlewares_setup import configure_middlewares

setup_logging()

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_TITLE,
    description=settings.PROJECT_DESCRIPTION,
    version=get_project_version(),
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)

configure_middlewares(app)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import sys

    import uvicorn

    debug: bool = False

    if "debug" in sys.argv[1:]:
        import debugpy

        debug = True

        debugpy.listen(("0.0.0.0", 5678))
        print("Aguardando o debugger conectar na porta 5678...")
        debugpy.wait_for_client()

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=not debug)
