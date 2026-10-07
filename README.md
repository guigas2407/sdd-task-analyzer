# sdd-task-analyzer

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Testes](https://img.shields.io/badge/pytest-33%20passed-brightgreen)

Módulo **TaskAnalyzer**, desenvolvido com Spec-Driven Development (SDD) e
geração de código assistida por IA, na disciplina Bootcamp III.

O módulo recebe uma lista de tarefas e calcula tempo médio de conclusão, taxa
de atraso e métricas por prioridade. Todo o processamento ocorre em memória.

## Status do build

| Item | Status |
| --- | --- |
| Test Harness (`pytest`) | 33 testes, 100% aprovados (execução local) |
| CI/CD (GitHub Actions) | Previsto para a Fase 3 |

## Estrutura

```
sdd-task-analyzer/
├── README.md                  # Este arquivo
├── CONTEXT_RULES.md           # Regras de governança para agentes de IA
├── .gitignore
├── requirements.txt           # Dependências autorizadas (pytest)
├── specs/
│   └── task_analyzer_spec.md  # Contrato SDD (fonte da verdade)
├── tests/
│   └── test_harness.py        # Test Harness com pytest
└── src/
    └── task_analyzer.py       # Código gerado via IA e homologado
```

## Como executar

Requer Python 3.11 ou superior.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

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
[`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md).

## Governança de IA

Todo prompt enviado ao assistente de IA começa com
[`CONTEXT_RULES.md`](CONTEXT_RULES.md) e a especificação. O código só entra
em `main` depois de passar no Test Harness e na revisão humana registrada no
Pull Request.

## Fluxo Git

- `main`: código estável e homologado.
- `feature/sdd-specification`: especificação e regras de contexto.
- `feature/test-harness`: suíte de testes.
- `feature/task-analyzer-impl`: implementação gerada via IA.

## Autor

Guilherme Meyer Soares — Análise e Desenvolvimento de Sistemas, Turma A.
