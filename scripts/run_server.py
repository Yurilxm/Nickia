"""Sobe o servidor Nickia na porta 8000."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import uvicorn

if __name__ == "__main__":
    print("Iniciando Nickia em http://localhost:8000")
    print("Aperte CTRL+C para parar.")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
