# Canvas files — instalacion local

Los canvas de Cursor **no viven en el repo git** por defecto. Deben copiarse a la carpeta de proyectos de Cursor en tu maquina.

## Windows

1. Abre esta carpeta en el Explorador de archivos:

   ```
   %USERPROFILE%\.cursor\projects\
   ```

2. Busca la subcarpeta de tu workspace (nombre codificado del repo, p. ej. contiene `cli-market-export-pit`).

3. Crea la carpeta `canvases` si no existe:

   ```
   %USERPROFILE%\.cursor\projects\<tu-workspace>\canvases\
   ```

4. Copia estos dos archivos desde `canvases/` del repo:

   - `lucuma-granola-us-opportunity.canvas.tsx`
   - `golden-lucuma-crunch-bom.canvas.tsx`

5. En Cursor: **Developer → Reload Window**

6. Abre el canvas desde el chat (enlace al `.canvas.tsx`) o desde el explorador de archivos de Cursor.

## Archivos

| Canvas | Contenido |
|--------|-----------|
| `lucuma-granola-us-opportunity.canvas.tsx` | Ficha de oportunidad CONDITIONAL GO |
| `golden-lucuma-crunch-bom.canvas.tsx` | Formulacion y BOM Golden Lucuma Crunch |

## Nota

Si el enlace del chat apunta a `/home/ubuntu/.cursor/...` es una ruta del agente cloud y **no funcionara en Windows**. Usa los archivos copiados localmente.
