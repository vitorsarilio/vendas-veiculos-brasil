"""Chave do cache dos PDFs no GitHub Actions: muda só quando a cópia local muda.

Hash da lista (mês, arquivo, sha256) do manifesto. Assim o cache de ~1 GB só é gravado
de novo quando chega um relatório novo ou um dos recentes é republicado.
"""

import hashlib
import json
import sys
from pathlib import Path

manifesto = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else "data/raw/_manifesto.json").read_text(encoding="utf-8"))
lista = json.dumps(manifesto["pdfs"], sort_keys=True).encode("utf-8")
print("pdfs-" + hashlib.sha256(lista).hexdigest()[:16])
