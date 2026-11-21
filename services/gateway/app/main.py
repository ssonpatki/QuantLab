"""API gateway: one public entry point that forwards /api/<service>/... to the right service."""
import os
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

ROUTES = {
    "market": os.getenv("MARKET_URL", "http://localhost:8001"),
    "backtest": os.getenv("BACKTEST_URL", "http://localhost:8002"),
    "ml": os.getenv("ML_URL", "http://localhost:8003"),
}
app = FastAPI(title="QuantLab Gateway")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
async def health():
    out = {}
    async with httpx.AsyncClient(timeout=5) as c:
        for name, url in ROUTES.items():
            try:
                out[name] = "up" if (await c.get(f"{url}/health")).status_code == 200 else "down"
            except httpx.HTTPError:
                out[name] = "down"
    return out


@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy(service: str, path: str, request: Request):
    base = ROUTES.get(service)
    if not base:
        raise HTTPException(404, f"Unknown service '{service}'")
    headers = {}
    if request.headers.get("content-type"):
        headers["content-type"] = request.headers["content-type"]
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.request(request.method, f"{base}/{path}", params=request.query_params,
                                content=await request.body(), headers=headers)
    except httpx.HTTPError:
        raise HTTPException(503, f"The {service} service is unreachable")
    return Response(r.content, r.status_code, media_type=r.headers.get("content-type"))
