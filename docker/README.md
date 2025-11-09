# MCP MixSearch Docker Setup

This directory contains Docker Compose configurations to run the MCP MixSearch server in different modes.

### Available Setups

### Development Setups (build locally)
- **MCP-only Mode** (`mcp/docker-compose.yml`): Pure MCP protocol with Streaming HTTP - REST API disabled
- **REST Mode** (`rest/docker-compose.yml`): Full REST API + MCP protocol support

### Production Setup (use published images)
- **MCP-only Mode** (`prod/docker-compose.yml`): Uses published GHCR image for production MCP-only deployment

## Prerequisites

- Docker and Docker Compose installed
- Git (for cloning dependencies)

## Quick Start

### Development Mode (Recommended for local development)

#### MCP-only Mode (Default)
For pure MCP protocol communication:

```bash
cd docker/mcp
docker-compose up --build -d
```

#### REST Mode
For full API access with health checks and documentation:

```bash
cd docker/rest
docker-compose up --build -d
```

### Production Mode (Uses published images)

**Note**: Production setups use the published Docker image from GHCR and run the package directly from the GitHub repository using `uvx mcp-mixsearch@git+https://github.com/geosp/mcp-mixsearch.git`.

#### Production MCP-only Mode
For production deployment using published images:

```bash
cd docker/prod
docker-compose up -d
```

### Check Status
```bash
# Development MCP-only
cd docker/mcp && docker-compose logs -f mcp-mixsearch

# Development REST
cd docker/rest && docker-compose logs -f mcp-mixsearch

# Production MCP-only
cd docker/prod && docker-compose logs -f mcp-mixsearch
```

### Stop Services
```bash
# Development MCP-only
cd docker/mcp && docker-compose down

# Development REST
cd docker/rest && docker-compose down

# Production MCP-only
cd docker/prod && docker-compose down
```

## Configuration

### Development Setups (Local building)
These setups build the Docker image locally and mount the source code for live development.

#### MCP-only Mode (docker-compose.yml)
The service is configured to:
- Build from the parent directory's Dockerfile
- Mount the project directory as `/app` for live code changes
- Expose port 3000 for MCP communication
- Run in Streaming HTTP mode (`MCP_ONLY=true`) for MCP protocol - **REST API endpoints are disabled**
- Use uvx to run the local MCP MixSearch package

#### REST Mode (docker-compose.rest.yml)
The service is configured to:
- Build from the parent directory's Dockerfile
- Mount the project directory as `/app` for live code changes
- Expose port 3000 for MCP communication
- Run with full REST API + MCP protocol support
- Use uvx to run the local MCP MixSearch package

### Production Setup (Published images)
This setup uses pre-built images from GitHub Container Registry for faster deployment.

#### MCP-only Mode (prod/docker-compose.yml)
The service is configured to:
- Use published image: `ghcr.io/geosp/mcp-mixsearch:main`
- Expose port 3000 for MCP communication
- Run in MCP-only mode (`--mode mcp`) for pure MCP protocol communication
- No source code mounting required

## Development

For development setups, the volume mount allows you to make changes to the code without rebuilding the container. Simply restart the service after changes:

```bash
# Development MCP-only mode
cd docker/mcp && docker-compose restart mcp-mixsearch

# Development REST mode
cd docker/rest && docker-compose restart mcp-mixsearch
```

**Note**: Production setups use published images and do not support live code reloading.

## Troubleshooting

- If you encounter permission issues, ensure Docker is running and you have proper permissions
- Check the logs with `docker-compose logs mcp-mixsearch` (or `docker-compose -f docker-compose.rest.yml logs mcp-mixsearch`) for detailed error messages
- The container uses uv for Python package management, which handles dependencies automatically
- **MCP-only mode**: When `MCP_ONLY=true`, REST API endpoints like `/health` are disabled. Only the `/mcp` endpoint is available for MCP protocol communication
- **REST mode**: Full API access available including `/health`, `/docs`, and `/mcp` endpoints
- **Production mode**: Uses `uvx` to run the package directly from the GitHub repository (`git+https://github.com/geosp/mcp-mixsearch.git`)
- **Versioned deployments**: Use specific version tags (e.g., `:v1.0.0`) for stable, immutable deployments instead of `:main` for bleeding-edge

## Environment Variables

You can add environment variables in the `docker-compose.yml` files under the `environment` section if needed for configuration.

- `MCP_ONLY=true`: Enables Streaming HTTP mode for MCP protocol communication (used in default `docker-compose.yml`)
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
# Development MCP-only mode
sudo podman-compose up --build -d
sudo podman-compose logs -f mcp-mixsearch
sudo podman-compose down

# Development REST mode
sudo podman-compose -f docker-compose.rest.yml up --build -d
sudo podman-compose -f docker-compose.rest.yml logs -f mcp-mixsearch
sudo podman-compose -f docker-compose.rest.yml down

# Production MCP-only mode
sudo podman-compose -f docker-compose.prod.yml up -d
sudo podman-compose -f docker-compose.prod.yml logs -f mcp-mixsearch
sudo podman-compose -f docker-compose.prod.yml down

# Production REST mode
sudo podman-compose -f docker-compose.prod.rest.yml up -d
sudo podman-compose -f docker-compose.prod.rest.yml logs -f mcp-mixsearch
sudo podman-compose -f docker-compose.prod.rest.yml down

# Production versioned mode
sudo podman-compose -f docker-compose.prod.v1.0.0.yml up -d
sudo podman-compose -f docker-compose.prod.v1.0.0.yml logs -f mcp-mixsearch
sudo podman-compose -f docker-compose.prod.v1.0.0.yml down
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
# Health check (REST mode only)
curl http://localhost:3000/health

# MCP endpoint (both modes)
curl http://localhost:3000/mcp

# Test search API (REST mode only)
curl -X POST "http://localhost:3000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI developments 2024",
    "limit": 5
  }'
```

## Semantic Versioning & Releases

The project uses [semantic versioning](https://semver.org/) for stable releases. Version tags follow the format `vMAJOR.MINOR.PATCH` (e.g., `v1.0.0`).

### Release Process

1. **Create a Git tag** for the release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions automatically**:
   - Builds and pushes Docker images with version tags
   - Creates multiple tags: `v1.0.0`, `v1.0`, `v1`, `latest`

3. **Use versioned images** in production:
   ```bash
   # Instead of :main, use specific version
   docker-compose -f docker-compose.prod.v1.0.0.yml up -d
   ```

### Available Version Tags

When you create a semantic version tag like `v1.2.3`, the following Docker image tags are created:
- `ghcr.io/geosp/mcp-mixsearch:v1.2.3` (full version)
- `ghcr.io/geosp/mcp-mixsearch:v1.2` (major.minor)
- `ghcr.io/geosp/mcp-mixsearch:v1` (major only)
- `ghcr.io/geosp/mcp-mixsearch:latest` (latest release)

### Creating Versioned Compose Files

To create a versioned compose file for any release:

```bash
# Replace VERSION with your desired version (e.g., v1.0.0)
VERSION=v1.0.0

# Copy the template
cp docker-compose.prod.yml docker-compose.prod.${VERSION}.yml

# Edit the image tag (change :main to :VERSION)
# You can do this manually or use sed:
sed -i "s|ghcr.io/geosp/mcp-mixsearch:main|ghcr.io/geosp/mcp-mixsearch:${VERSION}|g" docker-compose.prod.${VERSION}.yml
```

This creates `docker-compose.prod.v1.0.0.yml` that uses the stable `v1.0.0` image instead of the `main` branch.

### Branch vs Release Strategy

- **Branch-based** (`:main`): Latest development version, updated on every push
- **Release-based** (`:v1.0.0`): Stable, immutable versions for production

Use branch-based for development/testing, release-based for production stability.