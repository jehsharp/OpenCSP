# Testing Guide — Running `pytest` for OpenCSP + FFIAM

This guide documents every command needed to get `pytest` passing/running at the
repo root, in `example/`, and for the pyffiam tests after a fresh checkout.

Verified against: RHEL 9.x build node, Python 3.12.13 venv, `cee-build030`
(no NVIDIA GPU). A CUDA *toolkit/headers* are required to build the C++ backend,
but no GPU is needed for the CPU-only tests.

---

## 0. One-time repo/config changes (already committed to the working tree)

These source changes must exist for the commands below to work:

| File | Change |
|------|--------|
| `pyproject.toml` (root) | `[tool.pytest.ini_options]` adds `opencsp/test` + `independent/ffiam/pyffiam/tests` to `testpaths`, `pythonpath = ["independent/ffiam/pyffiam/src"]`, and a `requires_cuda` marker. |
| `independent/ffiam/pyffiam/pyproject.toml` | adds `pythonpath = ["src"]` and the `requires_cuda` marker so standalone pyffiam runs work. |
| `example/pytest.ini` | `testpaths` includes `../independent/ffiam/pyffiam/tests`; `pythonpath = .. ../independent/ffiam/pyffiam/src` (the `..` makes `import opencsp` resolve from `example/`). |
| `requirements.txt` | `numpy < 3.0.0`, `scipy <= 1.15.2`, plotly unversioned (pinned compatible via install step). |
| `independent/ffiam/ffiam/CMakeLists.txt` | CUDA language made conditional so `ffiam_lib_cpu` builds without nvcc; CUDA-dependent targets (`ffiam`, `ffiam_lib`, `ffiam_ue`) guarded; CUDA headers auto-discovered; OpenMP RPATH added to `ffiam_lib_cpu`. |

If the working tree is clean, the C++ build step (section 2) will fail without
the CMake patches.

---

## 1. Python virtual environment + dependencies

```bash
# (once) create and activate the venv
python3 -m venv .venv
source .venv/bin/activate

# (once) install opencsp deps
# NOTE: `pip install -r requirements.txt` FAILS -- pypylon is a known-broken
# package flagged in the requirements file. Install everything except it:
python -m pip install \
  "h5py>=3.10.0" \
  "matplotlib<=3.8.4" \
  "pyproj>=3.6.1" \
  "sympy>=1.12" \
  "pyexiftool>=0.5.6" \
  "opencv-contrib-python==4.11.0.86" \
  "python-pptx>=0.6.23" \
  "rawpy>=0.19.1" \
  "openpyxl>=3.1.2" \
  "pysolar>=0.11" \
  "ipykernel>=6.29.3"

# (once) upgrade plotly -- kaleido (image export) needs plotly >= 6.1.1
python -m pip install -U plotly
```

---

## 2. Build the FFIAM C++ backend (required for backend-dependent tests)

The Python CPU backend loads a compiled shared library that CMake copies into
`independent/ffiam/pyffiam/src/pyffiam/external/`.

### 2a. Load the CUDA module (headers + toolkit)

```bash
module load sems-cuda          # sets $CUDA_HOME, provides nvcc + headers
```

If the configure/build complains about a host-compiler mismatch (e.g.
`stddef.h: No such file or directory`), load the matching compiler that the
CUDA module was built against:

```bash
module load sems-gcc/13.2.0
```

### 2b. Configure + build the CPU-only backend

```bash
cd independent/ffiam/ffiam
rm -rf build-cpu               # re-run from scratch (avoids stale cache)
cmake -B build-cpu -DCMAKE_BUILD_TYPE=Release
cmake --build build-cpu --target ffiam_lib_cpu
```

Expected: `lib/libffiam_lib_cpu.so` is produced and the POST_BUILD step copies
it to `independent/ffiam/pyffiam/src/pyffiam/external/libffiam_lib_cpu.so`.

Verify:

```bash
ls -la ../pyffiam/src/pyffiam/external/libffiam_lib_cpu.so
cd ../..                       # back to repo root
```

If the library is missing, see section 4 (troubleshooting).

---

## 3. Run the tests

### Root level (opencsp + pyffiam)

```bash
pytest                        # run from repo root
```

### pyffiam only

```bash
pytest independent/ffiam/pyffiam/tests
```

### Example level

```bash
cd example
pytest
```

---

## 4. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No module named 'exiftool'` / `'cv2'` / `'matplotlib'` at collection | opencsp deps not installed — redo section 1. |
| `bash: pip: command not found` | activate the venv first (`source .venv/bin/activate`). |
| `No module named 'opencsp'` from `example/` | `example/pytest.ini` `pythonpath` must contain `..` (section 0). |
| `FFIAM CPU library not found at .../external/libffiam_lib_cpu.so` | backend not built — redo section 2. |
| `libomp.so: cannot open shared object file` at load | stale `.so` (no RPATH); rebuild with section 2b so the OpenMP RPATH is embedded. |
| `stddef.h: No such file or directory` during build | CUDA module / host gcc version mismatch — `module load sems-gcc/13.2.0` and reconfigure fresh. |
| `kaleido`/`Chrome` image-export errors in 18 plot tests | optional: plotly >= 6.1.1 required; static PNG export also needs Chrome installed. |
| `DockerParity` tests error/skip | expected without a local `ffiam` Docker image / no GPU. |
| `pypylon` fails to install | known-broken; not required for tests. Skipped in section 1. |

### Known remaining failures on a GPU-less dev node

These are environmental, not code bugs:

- **5 Docker parity errors** — need a `ffiam` Docker image + CUDA runtime.
- **~18 plot-export failures** — kaleido static export needs Google Chrome
  installed; these pass once Chrome is available.
- **CUDA tests** — auto-skip via the `requires_cuda` marker when no CUDA
  runtime/device is present.