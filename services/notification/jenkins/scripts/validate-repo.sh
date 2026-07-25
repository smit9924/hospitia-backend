#!/usr/bin/env bash

set -Eeuo pipefail

notification_service_dir="services/notification"

###############################################################################
# Validate required files
###############################################################################

required_files=(
    "${notification_service_dir}/pyproject.toml"
    "${notification_service_dir}/uv.lock"
    "${notification_service_dir}/jenkins/Dockerfile"
    "${notification_service_dir}/jenkins/.dockerignore"
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
    "${notification_service_dir}/notification"
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
    "${notification_service_dir}/notification/__init__.py"
    "${notification_service_dir}/notification/main.py"
)

for file in "${required_python_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
        printf 'Required Python file not found: %s\n' "${file}" >&2
        exit 1
    fi
done

printf 'Repository structure validation successful.\n'