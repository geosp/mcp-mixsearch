# Changelog

Notable changes for people who run or call mcp-mixsearch. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Add an entry under `Unreleased` in every pull request
that changes behavior, configuration or tool output.

## [Unreleased]

### Changed

- **Breaking for Docker deployments:** the Docker image now holds the app, installed at build time
  from `uv.lock`, so an image tag pins the code it runs and startup downloads nothing. The
  image's entrypoint is `mcp-mixsearch` (it was `uvx`), and it serves HTTP by default
  (`MCP_TRANSPORT=http`). To migrate, remove `command:` from your compose file, or keep only the
  server's options, for example `command: ["--port", "3001"]`. (#14)
- The image's Firefox is installed by the Playwright version locked in `uv.lock`; the Dockerfile
  no longer pins Playwright separately. (#14)
- `latest` is pushed only from `main`, and `main` and `latest` only from the tip of `main`.
  Release tags no longer move `latest`. (#14)
- The dev compose file (`docker/mcp/`) builds and runs the image without mounting the source;
  rebuild it to pick up code changes. (#14)

### Fixed

- `/health` and the MCP server info report the installed package version. They reported `1.0.0`
  on v1.1.0. (#14)

## [1.1.0] - 2026-11-17

### Added

- Search results are merged from several engines. The Brave Search API (when `BRAVE_API_KEY` is
  set), DDGS and DuckDuckGo HTML are queried in parallel. Their results are ranked by reciprocal
  rank fusion, and duplicate URLs are merged. (#11)
- Each result in `full_web_search` and `get_web_search_summaries` has an `Engines:` line naming
  the engines that returned it, for example `Engines: BraveAPI, DDGS`. The line follows
  `Description:`, and every other line is unchanged. (#11)
- `ENGINE_TIMEOUT_SECONDS` (default `10`): how long to wait for each engine queried in parallel.
  An engine that fails or times out is logged and skipped. (#11)

### Changed

- The Brave browser engine (headless Firefox) runs only as a fallback, when a web search returns
  fewer results than `limit`. Before, it was the third engine tried on every search that reached
  it. (#11)
- News, image and video searches no longer fall back to the DuckDuckGo HTML page or the Brave
  browser engine. Those returned plain web pages for every source. If DDGS fails, such a search
  now returns no results. (#11)
- A typical search now waits for the slowest engine queried in parallel, up to
  `ENGINE_TIMEOUT_SECONDS`, and sends more requests per search to the search engines. (#11)

### Removed

- The word-overlap quality check that picked one engine's results. (#11)

## [1.0.0]

The version in `pyproject.toml` before the first tagged release. It was never tagged.

- MCP tools `full_web_search`, `get_web_search_summaries` and `get_single_web_page_content`, over
  stdio or streamable HTTP, built on mcp-service-kit.
- Engines tried one at a time: the Brave Search API (with a key), DDGS, the Brave browser engine
  and DuckDuckGo HTML. The first result set that passed a quality check was used.
- Page content extraction with trafilatura. A shared headless Firefox renders pages that need
  JavaScript.
- Only public http(s) URLs are fetched.

[Unreleased]: https://github.com/geosp/mcp-mixsearch/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/geosp/mcp-mixsearch/releases/tag/v1.1.0
