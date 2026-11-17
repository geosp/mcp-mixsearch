# MCP MixSearch Docker Setup

This directory contains Docker Compose configurations to run the MCP MixSearch server over streamable HTTP.

### Available Setups

### Development Setups (build locally)
- **MCP Mode** (`mcp/docker-compose.yml`): MCP protocol over streamable HTTP

### Production Setup (use published images)
- **MCP Mode** (`prod/docker-compose.yml`): Uses published GHCR image for production deployment

## Prerequisites

- Docker and Docker Compose installed
- Git (for cloning dependencies)

## Quick Start

### Development Mode (Recommended for local development)

```bash
cd docker/mcp
docker-compose up --build -d
```

### Production Mode (Uses published images)

**Note**: Production setups use the published Docker image from GHCR and run the package directly from the GitHub repository using `uvx mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git`.

For production deployment using published images:

```bash
cd docker/prod
docker-compose up -d
```

### Check Status
```bash
# Development
cd docker/mcp && docker-compose logs -f mcp-mixsearch

# Production
cd docker/prod && docker-compose logs -f mcp-mixsearch
```

### Stop Services
```bash
# Development
cd docker/mcp && docker-compose down

# Production
cd docker/prod && docker-compose down
```

## Configuration

### Development Setups (Local building)
These setups build the Docker image locally and mount the source code for live development.

#### MCP Mode (mcp/docker-compose.yml)
The service is configured to:
- Build from the parent directory's Dockerfile
- Mount the project directory as `/app` for live code changes
- Expose port 3000 for MCP communication
- Run in streamable HTTP mode (`--mode http`) without auth (`MCP_AUTH_ENABLED=false`)
- Use uvx to run the local MCP MixSearch package

### Production Setup (Published images)
This setup uses pre-built images from GitHub Container Registry for faster deployment.

#### MCP Mode (prod/docker-compose.yml)
The service is configured to:
- Use published image: `ghcr.io/geosp/mcp-mixsearch:main`
- Expose port 3000 for MCP communication
- Run in streamable HTTP mode (`--mode http`) without auth (`MCP_AUTH_ENABLED=false`)
- No source code mounting required

## Development

For development setups, the volume mount allows you to make changes to the code without rebuilding the container. Simply restart the service after changes:

```bash
cd docker/mcp && docker-compose restart mcp-mixsearch
```

**Note**: Production setups use published images and do not support live code reloading.

## Troubleshooting

- If you encounter permission issues, ensure Docker is running and you have proper permissions
- **Port 3000 already allocated**: another container or process uses the host port. Pick another one with `MCP_HOST_PORT`, e.g. `MCP_HOST_PORT=3002 docker compose up -d`, and point clients at `http://localhost:3002/mcp`
- The compose files set `name: mcp-mixsearch`, so this project doesn't share the default `mcp`/`prod` project name with other compose projects (which would show their containers as "orphans")
- Check the logs with `docker-compose logs mcp-mixsearch` for detailed error messages
- The container uses uv for Python package management, which handles dependencies automatically
- **Endpoints**: `/mcp` for the MCP protocol and `/health` for health checks. There is no REST API
- **Auth**: The server has no auth provider, so with `MCP_AUTH_ENABLED` unset or `true` it refuses to start; keep `MCP_AUTH_ENABLED=false` and put an authenticating gateway in front if needed
- **Production mode**: Uses `uvx` to run the package directly from the GitHub repository (`git+https://github.com/geosp/mcp-mixsearch.git`)
- **Versioned deployments**: Use a release tag (e.g., `:v1.1.0`) instead of `:main` or `:latest`, which change on every merge. See [Semantic Versioning & Releases](#semantic-versioning--releases)

## Environment Variables

You can add environment variables in the `docker-compose.yml` files under the `environment` section if needed for configuration.

- `MCP_AUTH_ENABLED=false`: Serves HTTP without auth (required, since the server has no auth provider)
- `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`: Transport and bind address (the compose files pass `--mode http`)
- `UV_CACHE_DIR=/tmp/uv-cache`: Sets the cache directory for uv package manager

## Advanced: LXC Environment Setup

If you're running in an LXC container (advanced users), you may need special configuration:

### Prerequisites for LXC
- Podman with podman-compose installed
- LXC container configured for privileged operations

### LXC Configuration
Add these lines to your LXC config file:

```
lxc.cap.drop =
lxc.mount.auto = proc:rw sys:rw
```

### Running in LXC
Use `sudo` with podman-compose commands:

```bash
# Development mode
sudo podman-compose up --build -d
sudo podman-compose logs -f mcp-mixsearch
sudo podman-compose down

# Production mode
sudo podman-compose -f prod/docker-compose.yml up -d
sudo podman-compose -f prod/docker-compose.yml logs -f mcp-mixsearch
sudo podman-compose -f prod/docker-compose.yml down

# Production versioned mode
sudo podman-compose -f prod/docker-compose.v1.1.0.yml up -d
sudo podman-compose -f prod/docker-compose.v1.1.0.yml logs -f mcp-mixsearch
sudo podman-compose -f prod/docker-compose.v1.1.0.yml down
```

If you encounter container build failures in LXC, the privileged configuration above should resolve the `/proc` mount permission errors.

## VS Code MCP Integration

To use the MCP MixSearch server with VS Code, configure your `.vscode/mcp.json`:

```json
{
  "servers": {
    "mixsearch": {
      "type": "http",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

## Testing the Integration

You can test the MCP server connection:

```bash
# Health check
curl http://localhost:3000/health

# MCP endpoint
curl http://localhost:3000/mcp
```

## Semantic Versioning & Releases

The project uses [semantic versioning](https://semver.org/) for stable releases. Version tags follow the format `vMAJOR.MINOR.PATCH` (e.g., `v1.1.0`).

### Release Process

1. **Merge a pull request** that bumps `version` in `pyproject.toml` and moves the `Unreleased`
   entries in [CHANGELOG.md](../CHANGELOG.md) under the new version.

2. **Tag the merge commit on `main`** and push the tag:
   ```bash
   git switch main && git pull
   git tag -a v1.1.0 -m "v1.1.0"
   git push origin v1.1.0
   ```

3. **GitHub Actions** (`.github/workflows/docker-publish.yml`) builds the image and pushes it with
   the tags listed below.

4. **Create the GitHub release** from the changelog section:
   ```bash
   gh release create v1.1.0 --title "v1.1.0" --notes-file <file with the 1.1.0 section>
   ```

### Available Image Tags

| Event | Tags pushed |
| --- | --- |
| Merge (push) to `main` | `main`, `latest`, `sha-<short sha>` |
| Tag `v1.2.3` | `v1.2.3`, `1.2.3`, `1.2`, `1`, `latest`, `sha-<short sha>` |
| Pull request | Built, not pushed |

`latest` follows `main`; it doesn't mean "latest release". For a pinned deployment, use a full
version tag such as `v1.2.3` or `1.2.3`.

> **Note:** `prod/docker-compose.yml` starts the server with
> `uvx mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git`, which installs the code from
> the repository's default branch when the container starts. Pinning the image tag pins the
> runtime, not that code. To pin the code too, append the tag to the URL, for example
> `...mcp-mixsearch.git@v1.1.0`.

### Creating Versioned Compose Files

To create a versioned compose file for any release:

```bash
# Replace VERSION with your desired version (e.g., v1.1.0)
VERSION=v1.1.0

# Copy the production compose file
cp prod/docker-compose.yml prod/docker-compose.${VERSION}.yml

# Pin the image tag and the code (see the note above)
sed -i -e "s|ghcr.io/geosp/mcp-mixsearch:main|ghcr.io/geosp/mcp-mixsearch:${VERSION}|g" \
       -e "s|mcp-mixsearch.git\"|mcp-mixsearch.git@${VERSION}\"|g" prod/docker-compose.${VERSION}.yml
```

This creates `prod/docker-compose.v1.1.0.yml`, which runs the `v1.1.0` image and code instead of
`main`.

### Branch vs Release Strategy

- **Branch-based** (`:main`): Latest development version, updated on every push
- **Release-based** (`:v1.1.0`): Stable, immutable versions for production

Use branch-based for development/testing, release-based for production stability.