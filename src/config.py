import os
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

load_dotenv()

FULTec_BASE_URL = os.getenv("FULTec_BASE_URL", "").rstrip("/")
FULTec_TIMEOUT  = float(os.getenv("FULTec_TIMEOUT", "20"))

DEFAULT_SELECT  = ",".join([
    "idAbastecimento","idBico","situacao","idProduto","produto",
    "data","hora","dhRegistro","litragem","valorUnitario","encerrante",
    "valor","codVenda","idFuncionario","nomeFuncionario",
    "idVendedor","nomeVendedor","idNivel","nivel"
])
