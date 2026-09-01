#!/usr/bin/env bash
# Registers this package's local rosdep rules with the system rosdep sources list.
# Safe to re-run; does NOT call 'rosdep update' (the caller should, once).
set -euo pipefail

PKG_NAME="wled_ros_driver"
PRIORITY="${ROSDEP_SOURCE_PRIORITY:-50}"
SOURCES_DIR="${ROSDEP_SOURCES_DIR:-/etc/ros/rosdep/sources.list.d}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="${SCRIPT_DIR}/${PKG_NAME}.yaml"
LIST_FILE="${SOURCES_DIR}/${PRIORITY}-${PKG_NAME//_/-}.list"

if [[ ! -f "${RULES_FILE}" ]]; then
  echo "[${PKG_NAME}] ERROR: rules file not found: ${RULES_FILE}" >&2
  exit 1
fi

SUDO=""
[[ "${EUID}" -ne 0 ]] && SUDO="sudo"

${SUDO} mkdir -p "${SOURCES_DIR}"
printf 'yaml file://%s\n' "${RULES_FILE}" | ${SUDO} tee "${LIST_FILE}" >/dev/null

echo "[${PKG_NAME}] registered: ${RULES_FILE} -> ${LIST_FILE}"
