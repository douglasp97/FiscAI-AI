# FiscAI-AI

Aplicativo desktop MVP para auditoria fiscal de NF-e, com leitura de XML, regras tributárias, validação estrutural e relatórios em CSV/XLSX/PDF.

## Visão geral

Este projeto foi pensado como base para um sistema SaaS de auditoria fiscal, análise tributária e inteligência fiscal focado em empresas de autopeças. O MVP funciona como uma ferramenta desktop para:

- importar XMLs de NF-e
- extrair dados dos itens, tributos e cabeçalho
- validar estrutura e campos críticos
- aplicar regras fiscais iniciais
- sugerir oportunidades de recuperação tributária
- exportar o resultado em relatórios

## Requisitos

- Python 3.10+
- pip
- Windows 10/11 (para build do executável)

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## Execução do app

```bash
python main.py
```

## Regras fiscais implementadas no MVP

- ICMS: divergência de alíquota aplicada vs tabela NCM
- ICMS-ST: ausência de valor quando o NCM sugere ST
- PIS/COFINS: valores suspeitos, ausentes ou inconsistentes
- CFOP vs NCM: incompatibilidade básica de operação
- estrutura do XML: campos críticos ausentes e problemas de parsing

## Exemplo de XML

Há um arquivo de exemplo em:

```text
samples/sample_nfe.xml
```

## Build para Windows (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name FiscAI-AI main.py
```

O executável será gerado em `dist/FiscAI-AI.exe`.

## Estrutura do projeto

```text
main.py
parser.py
validators.py
fiscal_rules.py
exporters.py
samples/
requirements.txt
README.md
```

## Observações

- Este MVP é uma base sólida para evolução para SaaS.
- A validação fiscal real da SEFAZ/tributação exige integrações específicas e regras jurídicas mais profundas.
- Para produção, recomenda-se adicionar autenticação, multi-tenant, banco de dados, fila de processamento, storage de XML, e APIs de ERP.
