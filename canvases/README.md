# Canvas files — instalacion local

Los canvas de Cursor viven en `.cursor/projects/<workspace>/canvases/`, no en el repo git. Usa el script de instalacion para copiarlos automaticamente.

## Instalacion automatica

### Linux / Mac / Cloud Agent

Desde la raiz del repo:

```bash
bash scripts/install-canvases.sh
```

### Windows (PowerShell)

Desde la raiz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-canvases.ps1
```

Luego en Cursor: **Developer → Reload Window**.

## Instalacion manual (Windows)

1. Abre `%USERPROFILE%\.cursor\projects\`
2. Busca la carpeta de tu workspace (contiene `cli-market-export-pit`)
3. Crea `canvases\` si no existe
4. Copia los dos `.canvas.tsx` de esta carpeta
5. **Developer → Reload Window**

## Archivos

| Canvas | Contenido |
|--------|-----------|
| `lucuma-granola-us-opportunity.canvas.tsx` | Ficha CONDITIONAL GO — lucuma granola EE.UU. |
| `golden-lucuma-crunch-bom.canvas.tsx` | Formulacion y BOM Golden Lucuma Crunch |

## Nota

Enlaces del chat que apuntan a `/home/ubuntu/.cursor/...` son rutas del agente cloud y no funcionan en Windows. Tras ejecutar el script, abre los canvas desde tu carpeta local de proyectos.
