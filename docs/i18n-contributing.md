# Adding a new language to AdsReport

## Prerequisites

- A fork of the repository
- Basic understanding of JSON

## Steps

### 1. Copy the English template

```bash
cp adsreport/i18n/locales/en-US.json adsreport/i18n/locales/xx-YY.json
```

Replace `xx-YY` with the BCP 47 locale code (e.g., `es-ES`, `fr-FR`, `de-DE`).

### 2. Translate all values

Open the new file and translate every **value** (right side of the colon). **Never change the keys** (left side).

```json
{
  "common.save": "Guardar",   ← translate this
  "common.cancel": "Cancelar"
}
```

Preserve `{placeholders}` exactly as they appear — they will be replaced at runtime:

```json
"onboarding.step3.connection_ok": "Conectado! Se encontraron {count} cuenta(s)."
```

### 3. Register the locale

In `adsreport/constants.py`, add your locale to `SupportedLocale`:

```python
class SupportedLocale(str, Enum):
    PT_BR = "pt-BR"
    EN_US = "en-US"
    ES_ES = "es-ES"  # ← add this
```

### 4. Verify key parity

The CI checks that all locale files have exactly the same set of keys. Run it locally:

```bash
python -c "
import json
from pathlib import Path
locales = list(Path('adsreport/i18n/locales').glob('*.json'))
keys = [set(json.loads(p.read_text()).keys()) for p in locales]
ref = keys[0]
for p, ks in zip(locales[1:], keys[1:]):
    diff = ref.symmetric_difference(ks)
    if diff:
        print(f'Diff in {p}: {sorted(diff)}')
    else:
        print(f'{p}: OK')
"
```

### 5. Open a pull request

Title: `i18n: add es-ES locale`

The maintainers will review the translation and merge it.

## Notes

- If a key is missing in your locale at runtime, AdsReport falls back to `en-US`.
- You don't need to translate `docs/` or code comments — only the JSON files matter for the UI.
