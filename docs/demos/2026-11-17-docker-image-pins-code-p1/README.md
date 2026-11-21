# Manual check · Phase 01 of the Docker image plan

Plan: `docs/plans/2026-11-17-docker-image-pins-code`, phase 01 (image with the app built in).

- **Result:** pass before merge. The image starts and answers `/health` with no network, and a real search through `/mcp` returns fused results. The revision-label read after merge is still to do (below).
- **Machine:** AMD Ryzen AI Max+ 395 with Radeon 8060S (integrated GPU), Fedora Linux 44, kernel 7.3.3-200.fc44.x86_64, Docker 29.9.3.
- **Versions:** commit `f1a2f4e` (branch `feat/14-docker-image-pins-code`). In the image: Python 3.14.10, mcp-mixsearch 1.1.0, playwright 1.64.1, ddgs 9.16.1, fastmcp 4.1.4.
- **Who ran it:** an agent, delegated by the owner. The owner runs the post-merge step.
- **Commands and input:** below. The search query is the fixed `python programming language`, `limit` 5. No `BRAVE_API_KEY` was set.

## Before merge

1. Build: `docker build -t mcp-mixsearch:check .` (image size 2.78 GB).
2. Start with no network (R1):
   `docker run -d --name mms-off --network none -e MCP_AUTH_ENABLED=false mcp-mixsearch:check`, then from inside the container:
   `docker exec mms-off python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:3000/health').read().decode())"`.
3. Start normally and search through `/mcp` (R4):
   `docker run -d --name mms-on -e MCP_AUTH_ENABLED=false -p 127.0.0.1:3019:3000 mcp-mixsearch:check`, then a fastmcp `Client("http://127.0.0.1:3019/mcp")` calling `list_tools` and `get_web_search_summaries`.

### Observations

- Step 2: `/health` returned `{"status":"healthy","service":"mixsearch","version":"1.1.0"}` with `--network none`. The container log (33 lines) has no download, install or error lines.
- Step 3:
  - `list_tools` returned `full_web_search`, `get_single_web_page_content` and `get_web_search_summaries`.
  - The search took 1.8 s and returned 5 results. Their `Engines:` lines were `DDGS, DuckDuckGo` (3 results), `DuckDuckGo` (1) and `DDGS` (1).
  - The server log shows DuckDuckGo with 5 results in 0.98 s and DDGS with 5 results in 1.75 s. The browser fallback didn't run, because the parallel engines returned the 5 results asked for.
- Not observed here: the browser fallback path and BraveAPI. `.github/scripts/docker_smoke.sh` launches headless Firefox in the image.

## After merge (owner)

Read the revision label of the pushed `:main` image and compare it with the merge commit (R1):

```bash
docker pull ghcr.io/geosp/mcp-mixsearch:main
docker inspect -f '{{ index .Config.Labels "org.opencontainers.image.revision" }}' ghcr.io/geosp/mcp-mixsearch:main
git rev-parse origin/main
```

- **Result:** _to be filled in after merge_.
