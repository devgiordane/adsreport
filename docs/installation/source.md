# Running from source

This guide is for contributors and developers who want to run AdsReport directly from the repository.

## Prerequisites

- Python 3.11 or newer
- [Poetry](https://python-poetry.org/docs/#installation) 1.8+
- Git

## Clone and install

```bash
git clone https://github.com/adsreport/adsreport
cd adsreport
poetry install --all-extras
```

This creates a virtual environment and installs all dependencies including dev tools (pytest, ruff, mypy).

> 💡 `--all-extras` is required to install the `[dev]` optional group. Without it, `pytest`, `ruff`, and `mypy` won't be available.

## Run the dev server

```bash
poetry run adsreport start
```

Open [http://localhost:8050](http://localhost:8050). On first run, the onboarding wizard starts automatically.

Other CLI commands:

```bash
poetry run adsreport start --port 8080   # custom port
poetry run adsreport migrate             # run DB migrations
poetry run adsreport reset --confirm     # wipe and recreate the database
poetry run adsreport reset-password      # change admin password interactively
poetry run adsreport version
```

## Run the tests

```bash
poetry run pytest tests/unit/        # fast unit tests (~3s)
poetry run pytest tests/integration/ # integration tests
poetry run pytest                    # everything
```

## Lint and type-check

```bash
poetry run ruff check adsreport tests   # linter
poetry run ruff format adsreport tests  # formatter
poetry run mypy adsreport               # type checker
```

---

## Windows — system Python issue

On Windows, Python is sometimes installed into `C:\Program Files\Python3xx`, which requires
administrator privileges to modify. Poetry will fail with `PermissionError: [WinError 5]`
if it tries to use that installation as its virtual environment.

**Symptoms:**

```
PermissionError
[WinError 5] Acesso negado: 'C:\Program Files\Python314\Lib\site-packages\...'
Cannot install <package>.
```

**Fix — point Poetry to a user-writable Python:**

1. Find a Python installation under your user profile:

   ```powershell
   where.exe python
   ```

   Look for a path under `C:\Users\<you>\AppData\Local\` — that one is user-writable.
   Common locations:
   - `C:\Users\<you>\AppData\Local\Python\bin\python.exe` (pyenv-win)
   - `C:\Users\<you>\AppData\Local\Programs\Python\Python311\python.exe`

2. Tell Poetry to use it:

   ```powershell
   poetry env use "C:\Users\<you>\AppData\Local\Python\bin\python.exe"
   ```

   Poetry will create the virtualenv in its own cache directory
   (`C:\Users\<you>\AppData\Local\pypoetry\Cache\virtualenvs\`) where it has write access.

3. Then install and run normally:

   ```powershell
   poetry install
   poetry run adsreport start
   ```

> 💡 If you have multiple Python versions installed, `poetry env use` accepts any path.
> The version only needs to be 3.11 or newer.

---

## VS Code integration

After running `poetry install`, VS Code should detect the new virtualenv automatically.
If it doesn't, press `Ctrl+Shift+P` → **Python: Select Interpreter** and choose the
`adsreport-...` entry under the Poetry cache directory.
