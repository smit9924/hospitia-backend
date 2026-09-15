#!/usr/bin/env bash

set -Eeuo pipefail

dashboard_service_dir="services/dashboard"

###############################################################################
# Validate required files
###############################################################################

required_files=(
    "${dashboard_service_dir}/pyproject.toml"
    "${dashboard_service_dir}/uv.lock"
    "${dashboard_service_dir}/jenkins/Dockerfile"
    "${dashboard_service_dir}/jenkins/.dockerignore"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
        printf 'Required file not found: %s\n' "${file}" >&2
        exit 1
    fi
done

###############################################################################
# Validate required directories
###############################################################################

required_directories=(
    "${dashboard_service_dir}/dashboard"
)

for directory in "${required_directories[@]}"; do
    if [[ ! -d "${directory}" ]]; then
        printf 'Required directory not found: %s\n' "${directory}" >&2
        exit 1
    fi
done

###############################################################################
# Validate Python package
###############################################################################

required_python_files=(
    "${dashboard_service_dir}/dashboard/__init__.py"
    "${dashboard_service_dir}/dashboard/main.py"
)

for file in "${required_python_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
        printf 'Required Python file not found: %s\n' "${file}" >&2
        exit 1
    fi
done

printf 'Repository structure validation successful.\n'