# Pitchavi

Servicio de investigacion de inteligencia tecnologica con evidencia trazable.

El primer incremento implementa investigacion cientifica con OpenAlex:

1. Crea un `research_run`.
2. Conserva la respuesta cruda de OpenAlex de forma inmutable, identificada por SHA-256.
3. Normaliza publicaciones en registros de evidencia vinculados al `research_run`.
4. Enriquece esas publicaciones con Crossref sin duplicar DOI.

## Ejecutar

```powershell
$env:PYTHONPATH = "src"
python -m uvicorn pitchavi.api:app --reload
```

La API queda disponible en `http://127.0.0.1:8000/docs`.

## Ejemplo

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/v1/research-runs" `
  -ContentType "application/json" `
  -Body '{"query":"high-flavanol cocoa powder","target_market":"US","limit":10}'
```

Por defecto, los metadatos se guardan en `data/pitchavi.db` y las respuestas
crudas en `data/raw/`. Ambas rutas se pueden configurar con `PITCHAVI_DB_PATH`
y `PITCHAVI_RAW_DIR`. Para ingresar al pool de uso cortés de Crossref, configura
`PITCHAVI_CONTACT_EMAIL` con un correo de contacto.
