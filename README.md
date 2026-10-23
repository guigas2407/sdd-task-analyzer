# sdd-task-analyzer

[![CI](https://github.com/guigas2407/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/guigas2407/sdd-task-analyzer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/docker-python%3A3.11--slim-2496ED)

Módulo **TaskAnalyzer**, desenvolvido com Spec-Driven Development (SDD) e
geração de código assistida por IA, na disciplina Bootcamp III.

O módulo recebe uma lista de tarefas e calcula tempo médio de conclusão, taxa
de atraso e métricas por prioridade. Todo o processamento ocorre em memória.

## Status do build

| Item | Status |
| --- | --- |
| Test Harness (`pytest`) | 33 testes, 100% aprovados |
| CI/CD (GitHub Actions) | A cada push e Pull Request em `main` e `develop` |
| Docker | Testes executados em container `python:3.11-slim` |

## Estrutura

```
sdd-task-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Pipeline de CI (GitHub Actions)
├── Dockerfile                     # Imagem python:3.11-slim que roda o pytest
├── docker-compose.yml             # Orquestração: docker compose run --rm tests
├── .dockerignore
├── CONTEXT_RULES.md               # Regras de governança para agentes de IA
├── specs/
│   ├── system_design_document.pdf # SDD original (Fase 1)
│   ├── requirements.yaml          # Requisitos + rastreabilidade para os testes
│   └── task_analyzer_spec.md      # Contrato SDD v1.2 (fonte da verdade)
├── tests/
│   └── test_harness.py            # Test Harness com pytest
├── src/
│   └── task_analyzer.py           # Código gerado via IA e homologado
├── requirements.txt               # Dependências autorizadas (pytest)
├── .gitignore
└── README.md
```

## Como executar

### Com Docker (recomendado)

Não exige Python instalado, apenas o Docker.

```bash
docker build -t sdd-task-analyzer .
docker run --rm sdd-task-analyzer
```

Ou, com o Docker Compose, em um único comando:

```bash
docker compose run --rm tests
```

### Localmente

Requer Python 3.11 ou superior.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest tests/test_harness.py -v
```

Saída esperada nos dois casos: `33 passed`.

## Exemplo de uso

```python
from src.task_analyzer import analyze_tasks

tarefas = [
    {
        "id": "t1",
        "titulo": "Configurar ambiente",
        "prioridade": "ALTA",
        "data_criacao": "2026-03-01T08:00:00Z",
        "data_prazo": "2026-03-01T12:00:00Z",
        "data_conclusao": "2026-03-01T10:00:00Z",
        "status": "CONCLUIDA",
    },
]

resultado = analyze_tasks(tarefas)
print(resultado["tempo_medio_conclusao_horas"])  # 2.0
```

Para ver os logs estruturados:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="nivel=%(levelname)s modulo=%(name)s %(message)s",
)
```

## Contrato resumido

| Saída | Significado |
| --- | --- |
| `total_tarefas` | Tarefas recebidas |
| `total_concluidas` / `total_tarefas_analisadas` | Tarefas `CONCLUIDA` com data de conclusão |
| `total_pendentes` | Tarefas `PENDENTE` |
| `tempo_medio_conclusao_horas` | Média de horas, 2 casas decimais |
| `taxa_atraso_percentual` | % concluídas após o prazo |
| `metricas_por_prioridade` | Mesmas métricas para `BAIXA`, `MEDIA`, `ALTA` |

Datas com conclusão anterior à criação disparam `TaskValidationError`
(subclasse de `ValueError`). Listas sem tarefas concluídas retornam zeros e
um `logging.warning`. Detalhes em
[`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md); a ligação entre
cada requisito e seus testes está em
[`specs/requirements.yaml`](specs/requirements.yaml).

## Governança de IA

Todo prompt enviado ao assistente de IA começa com
[`CONTEXT_RULES.md`](CONTEXT_RULES.md) e a especificação. O código só entra
em `main` depois de passar no Test Harness, no pipeline de CI e na revisão
humana registrada no Pull Request.

## Fluxo Git

- `main`: código estável e homologado.
- `develop`: integração das funcionalidades antes da `main`.
- `feature/sdd-specification`: especificação e regras de contexto.
- `feature/test-harness`: suíte de testes.
- `feature/task-analyzer-impl`: implementação gerada via IA.
- `feature/ci-docker`: pipeline de CI e containerização (Fase 3).

## Autor

Guilherme Meyer Soares — Análise e Desenvolvimento de Sistemas, Turma A.
