# Especificação Técnica SDD — Módulo TaskAnalyzer

| Campo | Informação |
| --- | --- |
| Autor | Guilherme Meyer Soares |
| Curso | Análise e Desenvolvimento de Sistemas — Turma A |
| Disciplina | Bootcamp III |
| Versão | v1.1 (Contrato Executável — Fase 2) |

## Histórico de versões

| Versão | Fase | Mudança |
| --- | --- | --- |
| v1.0 | Fase 1 | Contrato original (`TaskAnalyzer.calcular_metricas`, `ValueError`). |
| v1.1 | Fase 2 | Alterações autorizadas pelo enunciado da Fase 2: função `analyze_tasks`, exceção `TaskValidationError` (subclasse de `ValueError`) e campos de saída `total_tarefas`, `total_concluidas`, `total_pendentes`. Esclarecimentos da seção 3.4. A assinatura da Fase 1 foi mantida como fachada. |

## 1. Propósito

O TaskAnalyzer processa métricas de produtividade de tarefas de um sistema de
gestão de projetos. Este documento é o contrato formal e a fonte da verdade
para a geração de código por agentes de IA.

Objetivos funcionais:

- **Tempo médio de conclusão:** duração média, em horas, entre `data_criacao`
  e `data_conclusao`.
- **Taxa de atraso:** percentual de tarefas concluídas depois de `data_prazo`.
- **Indicadores por prioridade:** as mesmas métricas segmentadas em `ALTA`,
  `MEDIA` e `BAIXA`.
- **Suporte à decisão:** dados estruturados para melhoria contínua da equipe.

## 2. Interface pública

```python
def analyze_tasks(tarefas: Sequence[Mapping[str, Any]]) -> ResultadoAnalise: ...

class TaskValidationError(ValueError): ...

class TaskAnalyzer:
    @staticmethod
    def calcular_metricas(tarefas: Sequence[Mapping[str, Any]]) -> ResultadoAnalise: ...
```

## 3. Contrato de dados

### 3.1 Entrada (cada tarefa é um dicionário)

| Campo | Tipo | Obrigatório | Restrições |
| --- | --- | --- | --- |
| `id` | `str` | Sim | Não vazio e único na lista. |
| `titulo` | `str` | Sim | Mínimo de 3 caracteres (ignorando espaços). |
| `prioridade` | `str` (enum) | Sim | `"BAIXA"`, `"MEDIA"` ou `"ALTA"`. |
| `data_criacao` | `datetime` ou ISO 8601 | Sim | Ex.: `2026-03-01T08:00:00Z`. |
| `data_prazo` | `datetime` ou ISO 8601 | Sim | Data limite para conclusão. |
| `data_conclusao` | `datetime`, ISO 8601 ou `None` | Não | `None` para tarefas não concluídas. |
| `status` | `str` (enum) | Sim | `"PENDENTE"`, `"CONCLUIDA"` ou `"CANCELADA"`. |

### 3.2 Saída (dicionário de retorno)

| Campo | Tipo | Regra |
| --- | --- | --- |
| `total_tarefas` | `int` | Quantidade de tarefas recebidas. |
| `total_concluidas` | `int` | Tarefas `CONCLUIDA` com `data_conclusao` preenchida. |
| `total_pendentes` | `int` | Tarefas com status `PENDENTE`. |
| `total_tarefas_analisadas` | `int` | Igual a `total_concluidas` (nome mantido da v1.0). |
| `tempo_medio_conclusao_horas` | `float` | Soma das horas (`data_conclusao - data_criacao`) ÷ concluídas, 2 casas decimais. |
| `taxa_atraso_percentual` | `float` | % (0.0 a 100.0) de concluídas com `data_conclusao > data_prazo`, 2 casas decimais. |
| `metricas_por_prioridade` | `dict` | Chaves `BAIXA`, `MEDIA`, `ALTA`, sempre presentes, cada uma com `total`, `tempo_medio_horas` e `taxa_atraso_percentual`. |

### 3.3 Regras de negócio

1. **Filtragem de status:** só entram nas médias e taxas as tarefas
   `CONCLUIDA` com `data_conclusao` não nula. `PENDENTE` e `CANCELADA` são
   desconsideradas nos cálculos.
2. **Invariante temporal:** `data_conclusao` não pode ser estritamente anterior
   a `data_criacao` em nenhum registro. A execução é interrompida com
   `TaskValidationError` e a mensagem
   `"Data de conclusão não pode ser anterior à data de criação da tarefa."`,
   com registro em `logging.error`.
3. **Prevenção de divisão por zero:** sem tarefas concluídas válidas (ou lista
   vazia), o retorno traz métricas zeradas (`0`, `0.0`, `0.0`) e um
   `logging.warning`, sem exceção.
4. **Validação de entrada:** registros que violem a seção 3.1 disparam
   `TaskValidationError` com mensagem explicativa e `logging.error`.

### 3.4 Esclarecimentos da v1.1

- Datas sem fuso horário são interpretadas como UTC, para que datas com e sem
  `Z` possam ser comparadas.
- Conclusão exatamente no prazo **não** é atraso (a regra usa `>`).
- Conclusão igual à criação é válida (duração 0h); apenas "estritamente
  anterior" é erro.
- A invariante temporal vale para qualquer status, conforme "qualquer registro
  fornecido" da regra 2.

## 4. Cenários de aceite (Dado — Quando — Então)

### Cenário 1 — Sucesso

**Dado** três tarefas:

| Tarefa | Prioridade | Criação | Prazo | Conclusão | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | ALTA | 2026-03-01T08:00:00 | 2026-03-01T12:00:00 | 2026-03-01T10:00:00 (2h, no prazo) | CONCLUIDA |
| 2 | ALTA | 2026-03-01T08:00:00 | 2026-03-01T10:00:00 | 2026-03-01T12:00:00 (4h, atrasada) | CONCLUIDA |
| 3 | MEDIA | 2026-03-01T08:00:00 | 2026-03-02T08:00:00 | — | PENDENTE |

**Quando** `analyze_tasks(tarefas)` for executada,
**Então** o resultado deve conter: `total_tarefas = 3`,
`total_concluidas = 2`, `total_pendentes = 1`, `total_tarefas_analisadas = 2`,
`tempo_medio_conclusao_horas = 3.0`, `taxa_atraso_percentual = 50.0` e, em
`ALTA`: `total = 2`, `tempo_medio_horas = 3.0`, `taxa_atraso_percentual = 50.0`.

### Cenário 2 — Exceção

**Dado** uma tarefa `CONCLUIDA` com criação em `2026-03-02T10:00:00` e
conclusão em `2026-03-01T10:00:00`,
**Quando** o analisador for executado,
**Então** deve disparar `TaskValidationError` (também um `ValueError`) com a
mensagem da regra 2 e registrar `logging.error`, sem crash não tratado.

### Cenário 3 — Casos de borda

**Dado** uma lista vazia, ou apenas com tarefas `PENDENTE`/`CANCELADA`,
**Quando** o analisador for executado,
**Então** deve retornar métricas `0.0` sem exceção e registrar
`logging.warning`.

## 5. Plano de homologação humana

1. Rodar `pytest` e exigir 100% de aprovação.
2. Auditar o código contra `CONTEXT_RULES.md` (bibliotecas, assinaturas,
   persistência, testes intocados).
3. Revisar legibilidade, PEP 8, type hints e docstrings.
4. Testar manualmente valores nulos, entradas atípicas e volume alto.
5. Aprovar o Pull Request e fazer o merge em `main`.

## 6. Versionamento

Git Flow simplificado: `main` guarda apenas código homologado; cada entrega
nasce em `feature/<nome>` e entra em `main` via Pull Request revisado.
