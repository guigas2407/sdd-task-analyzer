# CONTEXT_RULES — Governança de Contexto para Agentes de IA

> **Uso obrigatório:** todo prompt enviado a um agente de IA para gerar ou
> modificar o módulo TaskAnalyzer deve começar com o conteúdo integral deste
> arquivo, seguido de `specs/task_analyzer_spec.md`. Respostas que violarem
> qualquer regra abaixo são rejeitadas pelo desenvolvedor homologador.

## 1. Diretrizes arquiteturais (obrigatórias)

1. **Versão da linguagem:** Python 3.11 ou superior.
2. **Type hints totais:** anotações de tipo explícitas em todos os parâmetros,
   variáveis públicas e retornos de funções/métodos.
3. **Clean Code:** conformidade com a PEP 8 (linhas de até 79 caracteres) e
   Princípio da Responsabilidade Única (SRP).
4. **Documentação formal:** Google Style Docstrings em módulos, classes,
   métodos e exceções.
5. **Modularidade:** funções pequenas, coesas e com um único propósito.
6. **Tratamento estruturado de erros:** exceções específicas
   (`TaskValidationError`, subclasse de `ValueError`). Proibido
   `except Exception: pass` ou capturas genéricas.
7. **Observabilidade:** biblioteca padrão `logging`, mensagens estruturadas no
   formato `evento=<nome> chave=valor`:
   - `INFO` para fluxos normais;
   - `WARNING` para listas vazias ou sem tarefas concluídas;
   - `ERROR` para dados inconsistentes.

## 2. Proibições explícitas

1. **Bibliotecas externas:** proibido usar qualquer biblioteca de terceiros
   fora do `requirements.txt` (permitidos apenas a biblioteca padrão e pytest).
2. **Inalterabilidade dos testes:** proibido alterar, remover, flexibilizar ou
   burlar os testes de `tests/test_harness.py` para fazer o código passar.
3. **Respeito à arquitetura:** proibido modificar a estrutura de pastas e
   arquivos definida na especificação.
4. **Sem persistência lateral:** proibido gravar dados em banco, arquivos
   locais (CSV, JSON etc.) ou serviços externos. Processamento só em memória.
5. **Imutabilidade de assinaturas:** proibido alterar nomes e parâmetros das
   funções públicas do contrato sem autorização expressa.
6. **Geração com testes:** proibido criar funcionalidade sem o teste unitário
   correspondente.
7. **Sem código duplicado:** proibido gerar trechos redundantes, código morto
   ou comentários óbvios.
8. **Sem suposições não especificadas:** a IA não deve assumir regras de
   negócio que divirjam ou extrapolem o contrato. Em caso de ambiguidade, a IA
   deve apontá-la em vez de decidir sozinha.

## 3. Interface pública autorizada (Fase 2)

| Símbolo | Tipo | Observação |
| --- | --- | --- |
| `analyze_tasks(tarefas)` | função | Ponto de entrada exigido na Fase 2 |
| `TaskValidationError` | exceção | Subclasse de `ValueError` |
| `TaskAnalyzer.calcular_metricas(tarefas)` | método estático | Mantido da Fase 1; delega para `analyze_tasks` |

## 4. Regras de interação com a IA

- Prefixar todo prompt com este arquivo na íntegra.
- Os testes de `tests/test_harness.py` são aprovados pelo desenvolvedor e,
  depois do merge, só ele pode alterá-los.
- Toda resposta passa pelo Plano de Homologação Humana
  (`specs/task_analyzer_spec.md`, seção 5) antes do merge.
