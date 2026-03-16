# MemeCoin


## 1) Install Python (if needed)

### ✅ Option 1 – Use `pyenv` (recommended)
```bash
# Install pyenv (if not installed)
# (install method depends on your platform; on macOS you can use brew)
# brew install pyenv

# Install Python 3.12.10
pyenv install 3.12.10

# Use this version in the project directory
cd /path/to/MemeCoin
pyenv local 3.12.10
```

### ✅ Option 2 – Use an existing Python installation
If you already have Python 3.12 installed, run:
```bash
python3.12 --version
```

---

## 2) Create and activate a virtual environment

```bash
# In the project folder
python -m venv .venv

# Activate (macOS / Linux)
source .venv/bin/activate
```

---

## 3) Install required dependencies

After activating the venv:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

---

## 4) Verify the Python version inside the venv

```bash
python --version
```

It should return `Python 3.12.10` (or whatever version you installed via `pyenv`).

---
