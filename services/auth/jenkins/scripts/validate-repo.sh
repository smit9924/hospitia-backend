#!/usr/bin/env bash

set -Eeuo pipefail

auth_service_dir="services/auth"

###############################################################################
# Validate required files
###############################################################################

required_files=(
    "${auth_service_dir}/pyproject.toml"
    "${auth_service_dir}/uv.lock"
    "${auth_service_dir}/jenkins/Dockerfile"
    "${auth_service_dir}/jenkins/.dockerignore"
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
    "${auth_service_dir}/auth"
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
    "${auth_service_dir}/auth/__init__.py"
    "${auth_service_dir}/auth/main.py"
)

for file in "${required_python_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
        printf 'Required Python file not found: %s\n' "${file}" >&2
        exit 1
    fi
done

printf 'Repository structure validation successful.\n'