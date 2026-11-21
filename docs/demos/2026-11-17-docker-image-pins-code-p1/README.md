# Manual check · Phase 01 of the Docker image plan

Plan: `docs/plans/2026-11-17-docker-image-pins-code`, phase 01 (image with the app built in).

- **Result:** pass. Before merge, the image started and answered `/health` with no network, and a real search through `/mcp` returned fused results. After merge, the pushed `:main` carries the merge commit in its revision label.
- **Machine:** AMD Ryzen AI Max+ 395 with Radeon 8060S (integrated GPU), Fedora Linux 44, kernel 7.3.3-200.fc44.x86_64, Docker 29.9.3.
- **Versions:** commit `f1a2f4e` (branch `feat/14-docker-image-pins-code`). In the image: Python 3.14.10, mcp-mixsearch 1.1.0, playwright 1.64.1, ddgs 9.16.1, fastmcp 4.1.4.
- **Who ran it:** an agent, delegated by the owner, before merge. The owner and the agent ran the post-merge step.
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

Run on 2026-11-21 after PR #15 merged as `795ce58`:

- The owner's first pull came at the same moment as the publish run's push (finished 19:38:22 UTC). It got the old image (digest `sha256:0218b119…`), labelled `a7ac88c`, the commit before the merge.
- The registry then showed `main`, `latest` and `sha-795ce58` on one digest, `sha256:9841f31a…`. Each had the revision label `795ce58519cec4c409efa2562bedf205a3b21607` (`docker buildx imagetools inspect`).
- A second `docker pull` returned the same label, equal to `git rev-parse HEAD` on `main`.
- **Result:** pass. Publish run: `44941819809`.
