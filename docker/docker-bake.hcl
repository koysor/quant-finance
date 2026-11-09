# Buildx bake file: builds the shared base image and the four app images in
# one invocation. Each app is built FROM the base image of the same build (a
# "target:" context), never from a base image pulled from the registry, so a
# dependency change is always built into, and tested with, the apps.
#
# Local build (images are loaded into Docker, nothing is pushed):
#   docker buildx bake -f docker/docker-bake.hcl --load
#
# CI sets TAG to the commit SHA, PUSH_LATEST on main, and GHA_CACHE.

variable "IMAGE_PREFIX" {
  default = "ghcr.io/koysor/quant-finance"
}

# Image tag; CI uses the full commit SHA so each deploy names an exact build
variable "TAG" {
  default = "dev"
}

# Also tag images "latest" (main branch only)
variable "PUSH_LATEST" {
  default = false
}

# Use the GitHub Actions cache (only available inside GitHub Actions)
variable "GHA_CACHE" {
  default = false
}

variable "APPS" {
  default = ["quant-finance", "options", "fixed-income", "portfolio-management"]
}

function "image_tags" {
  params = [name]
  result = concat(
    ["${IMAGE_PREFIX}/${name}:${TAG}"],
    PUSH_LATEST ? ["${IMAGE_PREFIX}/${name}:latest"] : []
  )
}

function "cache_from" {
  params = [name]
  result = GHA_CACHE ? ["type=gha,scope=${name}"] : []
}

function "cache_to" {
  params = [name]
  result = GHA_CACHE ? ["type=gha,mode=max,scope=${name}"] : []
}

group "default" {
  targets = concat(["base"], APPS)
}

target "_common" {
  context = "."
  labels = {
    "org.opencontainers.image.source"   = "https://github.com/koysor/quant-finance"
    "org.opencontainers.image.revision" = TAG
  }
}

target "base" {
  inherits   = ["_common"]
  dockerfile = "docker/Dockerfile.base"
  tags       = image_tags("base")
  cache-from = cache_from("base")
  cache-to   = cache_to("base")
}

target "app" {
  name       = app
  matrix     = { app = APPS }
  inherits   = ["_common"]
  dockerfile = "docker/Dockerfile.${app}"
  # FROM ${BASE_IMAGE} resolves to the "base" target built above
  contexts   = { quant-finance-base = "target:base" }
  args       = { BASE_IMAGE = "quant-finance-base" }
  tags       = image_tags(app)
  cache-from = cache_from(app)
  cache-to   = cache_to(app)
}
