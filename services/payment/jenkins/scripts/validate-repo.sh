#!/usr/bin/env bash

set -Eeuo pipefail

payment_service_dir="services/payment"

###############################################################################
# Validate required files
###############################################################################

required_files=(
    "${payment_service_dir}/pyproject.toml"
    "${payment_service_dir}/uv.lock"
    "${payment_service_dir}/jenkins/Dockerfile"
    "${payment_service_dir}/jenkins/.dockerignore"
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
    "${payment_service_dir}/payment"
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
    "${payment_service_dir}/payment/__init__.py"
    "${payment_service_dir}/payment/main.py"
)

for file in "${required_python_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
        printf 'Required Python file not found: %s\n' "${file}" >&2
        exit 1
    fi
done

printf 'Repository structure validation successful.\n'