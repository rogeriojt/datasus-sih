# DATASUS SIH

Coleta e painel de procedimentos do SIH/SUS (cirurgias cardíacas e
transplantes), organizados por **ano/mês de competência** (processamento
da AIH) e apresentados num painel Streamlit.

> **Nota sobre a dimensão de tempo**: os dados são organizados pelo
> ano/mês de **competência** (processamento/faturamento da AIH), que é
> a mesma dimensão de tempo usada por padrão no TabNet do DATASUS. Isso
> garante que os números do painel sejam diretamente comparáveis aos
> consultados manualmente no TabNet.

## Arquitetura

Todo o estado do projeto vive num único banco **SQLite**
(`data/sih.db`), com modo WAL para leituras/escritas concorrentes
seguras. Dado bruto (procedimentos coletados) e dado enriquecido
(nomes de estabelecimento e de município) ficam sempre em tabelas
separadas — o enriquecimento é feito por `JOIN` na hora da consulta
(`datasus/consultas.py`), nunca gravado junto com o dado bruto.

O download de cada competência distingue explicitamente três estados:
- **sucesso**: baixou e filtrou normalmente (pode ter zero linhas
  filtradas, se não houve nenhum procedimento monitorado no período).
- **suspeita_falha_silenciosa**: o download bruto voltou vazio (nem uma
  única AIH para a UF inteira no mês inteiro) — entra automaticamente
  na fila de nova tentativa, em vez de ser tratado como sucesso
  permanente.
- **falha**: todas as tentativas de download geraram erro.

## Estrutura do projeto

```
datasus-sih/
├── app.py                    # Painel Streamlit
├── cli.py                    # Interface de linha de comando única
├── datasus/
│   ├── settings.py           # Caminhos, ano-base, cores
│   ├── db.py                 # Schema e acesso ao SQLite
│   ├── codigos.py             # Normalização de códigos (puro, testável)
│   ├── download.py             # Fala com o pysus (único módulo com rede)
│   ├── coleta.py                # Pipeline: baixar → organizar → persistir
│   ├── catalogo.py               # Importa data/procedimentos.xlsx
│   ├── estabelecimentos.py        # Cache de nomes (API CNES)
│   ├── municipios.py               # Cache de municípios (API IBGE)
│   ├── consultas.py                 # Consultas de leitura
│   └── exportar.py                   # Excel / PDF
├── data/
│   ├── procedimentos.xlsx             # Catálogo de códigos SIGTAP monitorados
│   └── sih.db                          # Banco SQLite (versionado no git)
├── tests/                              # Testes automatizados (pytest)
├── launchers/                          # Atalhos para uso local (Windows/Mac)
└── .github/workflows/coletar.yml       # Coleta automática diária
```

## Uso local

Na primeira vez, rode `launchers/configurar_ambiente.bat` (Windows) ou
`.command` (Mac/Linux). Depois disso:

- **Abrir o painel**: `launchers/iniciar_painel.bat` / `.command`
- **Atualizar os dados**: `launchers/atualizar_dados.bat` / `.command`

Ou diretamente pela linha de comando (com o `.venv` ativado):

```bash
python cli.py importar-procedimentos      # sincroniza data/procedimentos.xlsx
python cli.py coletar                     # coleta o ano-base (incremental)
python cli.py retentar-falhas             # reprocessa falhas e suspeitas
python cli.py atualizar-municipios        # cache de nomes de município (IBGE)
python cli.py corrigir-nomes              # cache de nomes de estabelecimento (CNES)
python cli.py cobertura                   # relatório de cobertura do ano-base
python cli.py integridade                 # confere consistência dos dados
python cli.py resetar --confirmar         # apaga os dados coletados
streamlit run app.py                      # abre o painel
python -m pytest tests/ -v                # roda os testes
```

## Publicar na nuvem (GitHub + Streamlit Community Cloud)

1. Crie um repositório no GitHub e envie este projeto.
2. Em **Settings → Actions → General → Workflow permissions**, marque
   **Read and write permissions** (necessário para a coleta automática
   salvar os dados).
3. A coleta roda sozinha todo dia via `.github/workflows/coletar.yml`
   (ou manualmente pela aba **Actions**).
4. Publique o painel em [share.streamlit.io](https://share.streamlit.io),
   apontando para `app.py`.

## Ano-base

O painel consolida um ano por vez (`config` em `datasus/settings.py`).
Por padrão, o ano-base é o ano anterior ao atual, avançando a partir de
fevereiro (`MES_VIRADA`) — tempo suficiente para o DATASUS publicar a
competência de dezembro do ano anterior.

## O catálogo de procedimentos

O projeto já vem com o catálogo completo em `data/procedimentos.xlsx`:
91 procedimentos monitorados — 86 cirurgias cardíacas (pediátricas/
congênitas, valvares, aorta e revascularização) e 5 transplantes
(coração, fígado e rim). Para adicionar, remover ou desativar algum
código, edite essa planilha e rode `python cli.py importar-procedimentos`.
