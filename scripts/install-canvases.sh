#!/usr/bin/env bash
# Instala los canvas del repo en la carpeta de proyectos de Cursor.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/canvases"
CANVAS_FILES=(
  "lucuma-granola-us-opportunity.canvas.tsx"
  "golden-lucuma-crunch-bom.canvas.tsx"
)

resolve_target_dir() {
  if [[ -n "${CURSOR_CANVASES_DIR:-}" ]]; then
    echo "${CURSOR_CANVASES_DIR}"
    return
  fi

  local projects_root="${HOME}/.cursor/projects"
  if [[ ! -d "${projects_root}" ]]; then
    echo "No existe ${projects_root}. Define CURSOR_CANVASES_DIR manualmente." >&2
    exit 1
  fi

  # Preferir carpeta cuyo nombre contiene el basename del repo.
  local repo_name
  repo_name="$(basename "${REPO_ROOT}")"
  local match=""
  while IFS= read -r dir; do
    if [[ "${dir}" == *"${repo_name}"* ]]; then
      match="${dir}"
      break
    fi
  done < <(find "${projects_root}" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort)

  if [[ -z "${match}" ]]; then
    # Fallback: entorno cloud de Cursor (workspace codificado como "workspace").
    if [[ -d "${projects_root}/workspace" ]]; then
      match="workspace"
    else
      match="$(find "${projects_root}" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | head -n 1)"
    fi
  fi

  if [[ -z "${match}" ]]; then
    echo "No se encontro workspace en ${projects_root}." >&2
    exit 1
  fi

  echo "${projects_root}/${match}/canvases"
}

TARGET_DIR="$(resolve_target_dir)"
mkdir -p "${TARGET_DIR}"

for file in "${CANVAS_FILES[@]}"; do
  src="${SOURCE_DIR}/${file}"
  if [[ ! -f "${src}" ]]; then
    echo "Falta archivo fuente: ${src}" >&2
    exit 1
  fi
  cp "${src}" "${TARGET_DIR}/${file}"
  echo "OK  ${TARGET_DIR}/${file}"
done

echo ""
echo "Canvas instalados. En Cursor: Developer -> Reload Window"
