# Cantus ↔ Notion Sync (galería bestiario)

La web de **Cantus Alarum Nigrarum** se genera desde Notion como **archivo de solo lectura** (estilo bestiario) y se publica en GitHub Pages.

## Qué hace el pipeline

1. Lee la base **Personajes Canon** y **Facciones Canónicas**.
2. Lee páginas de lore (Pre-Historia, Escalas de poder).
3. Genera HTML estático en `/Cantus-Alarum-Nigrarum/`:
   - `personajes/` — galería + ficha por personaje (con retrato si existe)
   - `facciones/` — galería + ficha por facción
   - `cosmologia.html`, `escalas.html`
4. Se ejecuta **automáticamente el día 1 y el 16 de cada mes** (~cada 15 días), o a mano desde Actions.

## Configuración (una sola vez)

### 1. Crear integración en Notion

1. Entra en [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **New integration** → nombre `Cantus Sync` → workspace tuyo
3. Copia el **Internal Integration Secret** (empieza por `ntn_` o `secret_`)

### 2. Compartir páginas/bases con la integración

En cada base o página canónica:

- Personajes Canon (database)
- Facciones Canonicas (database)
- Pre-Historia
- Escalas de poder, tipos y rangos

Menú `···` → **Connections** → añade **Cantus Sync**.

### 3. Copiar IDs

- **Database ID**: abre la base en el navegador. En la URL:
  `https://www.notion.so/xxxxx?v=...` → el bloque de 32 hex (a veces con guiones) es el ID.
- **Page ID**: igual, al final de la URL de la página.

IDs conocidos de tu workspace (referencia):

| Recurso | ID (sin guiones o con, ambos valen) |
|---------|--------------------------------------|
| Personajes Canon (database) | `2d9cc3f68d7c803d810fcfa65bdc6748` |
| Facciones Canonicas (database) | `2d9cc3f68d7c8090992ad39a2befc0ed` |
| Pre-Historia | `2f9cc3f68d7c800ea824e36a62854ecd` |
| Escalas de poder | `306cc3f68d7c8064891fd641eb6d8f93` |

### 4. Secrets en GitHub

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Name | Value |
|------|--------|
| `NOTION_TOKEN` | el secret de la integración |
| `NOTION_CHARACTERS_DB` | ID base Personajes |
| `NOTION_FACTIONS_DB` | ID base Facciones |
| `NOTION_PREHISTORIA_ID` | ID página Pre-Historia |
| `NOTION_POWER_ID` | ID página Escalas |

### 5. Primera sincronización

**Actions** → **Sync Cantus from Notion** → **Run workflow**.

Cuando termine, la galería estará en:

https://obsidiannexus.github.io/Cantus-Alarum-Nigrarum/personajes/

## Notas

- Notion sigue siendo la **única fuente editable**.
- La web **no** permite editar el canon.
- Los retratos usan URLs firmadas de Notion; en cada sync se refrescan.
- Si añades personajes nuevos en Notion, aparecerán en el siguiente ciclo (o al lanzar el workflow a mano).
