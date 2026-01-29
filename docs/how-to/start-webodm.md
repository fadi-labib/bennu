# Start WebODM and Process Images

Spin up the WebODM photogrammetry server and process geotagged aerial images
into orthophotos, elevation models, 3D meshes, and point clouds.

!!! abstract "Prerequisites"

    - [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed
    - A folder of geotagged JPEG images (see [Transfer Images](transfer-images.md))

## Start WebODM

```bash
cd ground/odm
docker compose up -d
```

This launches three services:

| Service  | Description                        | Port |
|----------|------------------------------------|------|
| `webapp` | WebODM web interface               | 8000 |
| `db`     | PostgreSQL database                | --   |
| `worker` | NodeODM processing engine          | 3000 |

Once the containers are running, open **<http://localhost:8000>** in your
browser.

## Process via Web UI

1. Log in to WebODM (create an account on first launch)
2. Click **Add Project** and give it a name
3. Click **Select Images** and upload your geotagged JPEGs
4. Click **Start Task** to begin processing
5. When complete, download results (orthophoto, 3D model, point cloud)

The web UI shows real-time progress and lets you preview results in a built-in
map viewer.

## Process via CLI

For scripted or headless workflows, use the CLI wrapper:

```bash
./ground/odm/process.sh <image_folder> [profile]
```

### Examples

Process with the default `survey_standard` profile:

```bash
./ground/odm/process.sh ./captures_20260308_143022
```

Process with a custom profile:

```bash
./ground/odm/process.sh ./captures_20260308_143022 high_detail
```

Profiles are JSON files in `ground/odm/profiles/` that map to ODM CLI flags.

### Output Files

Results are written to `<image_folder>/odm_output/`:

| Directory                | Output                          | Format |
|--------------------------|---------------------------------|--------|
| `odm_orthophoto/`        | Orthophoto (georeferenced mosaic) | `.tif` |
| `odm_dem/`               | Digital Surface Model           | `.tif` |
| `odm_texturing/`         | Textured 3D mesh                | `.obj` |
| `odm_georeferencing/`    | Georeferenced point cloud       | `.laz` |

!!! tip "Large Datasets"

    For large datasets (hundreds of images), the CLI approach is faster than the
    web UI because it avoids the upload step -- images are mounted directly from
    disk into the Docker container.

## Stop WebODM

```bash
cd ground/odm
docker compose down
```

Data is persisted in Docker volumes (`webodm_data`, `webodm_db`), so your
projects and results survive restarts.
