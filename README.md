# FULTEC Dashboard (Streamlit)

## Instalação
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edite o token
streamlit run app/Home.py
```

## Estrutura
```
fultec_dash/
├─ .env
├─ requirements.txt
├─ streamlit.toml
├─ src/
│  ├─ config.py
│  ├─ fultec_api.py
│  ├─ transforms.py
│  ├─ ui_components.py
│  └─ utils.py
└─ app/
   ├─ Home.py
   └─ pages/
      ├─ 01_Visão_Geral.py
      ├─ 02_Por_Vendedor.py
      ├─ 03_Tempo_Real.py
      └─ 04_Produtos.py
```

## Autenticação automática (/token)
Defina no `.env`:

```
FULTec_USER=seu_usuario
FULTec_PASS=sua_senha
FULTec_CNPJ=00000000000000
```
O app requisita e renova o token automaticamente quando receber 401.
