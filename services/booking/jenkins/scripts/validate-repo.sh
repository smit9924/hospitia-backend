#!/usr/bin/env bash

set -Eeuo pipefail

booking_service_dir="services/booking"

###############################################################################
# Validate required files
###############################################################################

required_files=(
    "${booking_service_dir}/pyproject.toml"
    "${booking_service_dir}/uv.lock"
    "${booking_service_dir}/jenkins/Dockerfile"
    "${booking_service_dir}/jenkins/.dockerignore"
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
    "${booking_service_dir}/booking"
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
    "${booking_service_dir}/booking/__init__.py"
    "${booking_service_dir}/booking/main.py"
)

for file in "${required_python_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
        printf 'Required Python file not found: %s\n' "${file}" >&2
        exit 1
    fi
done

printf 'Repository structure validation successful.\n'