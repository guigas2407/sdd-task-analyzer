"""Test Harness do módulo TaskAnalyzer.

Traduz os cenários de aceite da especificação
(``specs/task_analyzer_spec.md``) em testes automatizados com pytest.
Nenhum código gerado por IA é aceito sem 100% de aprovação nesta suíte.
"""

from __future__ import annotations

import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.task_analyzer import (  # noqa: E402
    MSG_DATA_INCONSISTENTE,
    TaskAnalyzer,
    TaskValidationError,
    analyze_tasks,
)

Tarefa = dict[str, Any]
MENSAGEM_ESPERADA: str = re.escape(MSG_DATA_INCONSISTENTE)


def criar_tarefa(**campos: Any) -> Tarefa:
    """Monta uma tarefa válida, sobrescrevendo os campos informados.

    Args:
        **campos: Campos a sobrescrever no registro padrão.

    Returns:
        Registro de tarefa no formato do contrato de entrada.
    """
    tarefa: Tarefa = {
        "id": "t-padrao",
        "titulo": "Tarefa padrão",
        "prioridade": "MEDIA",
        "data_criacao": "2026-03-01T08:00:00",
        "data_prazo": "2026-03-01T12:00:00",
        "data_conclusao": None,
        "status": "PENDENTE",
    }
    tarefa.update(campos)
    return tarefa


@pytest.fixture
def tarefas_cenario_1() -> list[Tarefa]:
    """Dados exatos do Cenário 1 da especificação."""
    return [
        criar_tarefa(
            id="t1",
            titulo="Tarefa 1",
            prioridade="ALTA",
            data_criacao="2026-03-01T08:00:00",
            data_prazo="2026-03-01T12:00:00",
            data_conclusao="2026-03-01T10:00:00",
            status="CONCLUIDA",
        ),
        criar_tarefa(
            id="t2",
            titulo="Tarefa 2",
            prioridade="ALTA",
            data_criacao="2026-03-01T08:00:00",
            data_prazo="2026-03-01T10:00:00",
            data_conclusao="2026-03-01T12:00:00",
            status="CONCLUIDA",
        ),
        criar_tarefa(
            id="t3",
            titulo="Tarefa 3",
            prioridade="MEDIA",
            data_criacao="2026-03-01T08:00:00",
            data_prazo="2026-03-02T08:00:00",
            data_conclusao=None,
            status="PENDENTE",
        ),
    ]


# ---------------------------------------------------------------------------
# Cenário 1 — Sucesso: tarefas válidas e métricas precisas
# ---------------------------------------------------------------------------


def test_cenario_1_totais(tarefas_cenario_1: list[Tarefa]) -> None:
    resultado = analyze_tasks(tarefas_cenario_1)
    assert resultado["total_tarefas"] == 3
    assert resultado["total_concluidas"] == 2
    assert resultado["total_pendentes"] == 1
    assert resultado["total_tarefas_analisadas"] == 2


def test_cenario_1_tempo_medio_geral(tarefas_cenario_1: list[Tarefa]) -> None:
    resultado = analyze_tasks(tarefas_cenario_1)
    assert resultado["tempo_medio_conclusao_horas"] == 3.0


def test_cenario_1_taxa_atraso_geral(tarefas_cenario_1: list[Tarefa]) -> None:
    assert analyze_tasks(tarefas_cenario_1)["taxa_atraso_percentual"] == 50.0


def test_cenario_1_metricas_prioridade_alta(
    tarefas_cenario_1: list[Tarefa],
) -> None:
    metricas = analyze_tasks(tarefas_cenario_1)["metricas_por_prioridade"]
    assert metricas["ALTA"] == {
        "total": 2,
        "tempo_medio_horas": 3.0,
        "taxa_atraso_percentual": 50.0,
    }


def test_cenario_1_prioridades_sem_concluidas_zeradas(
    tarefas_cenario_1: list[Tarefa],
) -> None:
    metricas = analyze_tasks(tarefas_cenario_1)["metricas_por_prioridade"]
    zeradas = {
        "total": 0,
        "tempo_medio_horas": 0.0,
        "taxa_atraso_percentual": 0.0,
    }
    assert set(metricas) == {"BAIXA", "MEDIA", "ALTA"}
    assert metricas["MEDIA"] == zeradas
    assert metricas["BAIXA"] == zeradas


def test_cenario_1_fachada_fase_1_equivalente(
    tarefas_cenario_1: list[Tarefa],
) -> None:
    esperado = analyze_tasks(tarefas_cenario_1)
    assert TaskAnalyzer.calcular_metricas(tarefas_cenario_1) == esperado


# ---------------------------------------------------------------------------
# Cenário 2 — Exceção: datas inconsistentes (conclusão < criação)
# ---------------------------------------------------------------------------


@pytest.fixture
def tarefa_invalida() -> Tarefa:
    """Dados exatos do Cenário 2 da especificação."""
    return criar_tarefa(
        id="t-invalida",
        titulo="Tarefa Invalida",
        data_criacao="2026-03-02T10:00:00",
        data_prazo="2026-03-03T10:00:00",
        data_conclusao="2026-03-01T10:00:00",
        status="CONCLUIDA",
    )


def test_cenario_2_dispara_task_validation_error(
    tarefa_invalida: Tarefa,
) -> None:
    with pytest.raises(TaskValidationError, match=MENSAGEM_ESPERADA):
        analyze_tasks([tarefa_invalida])


def test_cenario_2_erro_e_um_value_error(tarefa_invalida: Tarefa) -> None:
    with pytest.raises(ValueError):
        analyze_tasks([tarefa_invalida])


def test_cenario_2_registra_log_de_erro(
    tarefa_invalida: Tarefa, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.ERROR), pytest.raises(TaskValidationError):
        analyze_tasks([tarefa_invalida])
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_cenario_2_interrompe_mesmo_com_tarefas_validas(
    tarefas_cenario_1: list[Tarefa], tarefa_invalida: Tarefa
) -> None:
    with pytest.raises(TaskValidationError):
        analyze_tasks([*tarefas_cenario_1, tarefa_invalida])


def test_cenario_2_valida_datas_de_qualquer_status() -> None:
    tarefa = criar_tarefa(
        id="t-pendente",
        data_criacao="2026-03-02T10:00:00",
        data_conclusao="2026-03-01T10:00:00",
        status="PENDENTE",
    )
    with pytest.raises(TaskValidationError, match=MENSAGEM_ESPERADA):
        analyze_tasks([tarefa])


# ---------------------------------------------------------------------------
# Casos de borda — entradas vazias, sem concluídas e limites
# ---------------------------------------------------------------------------


def _assert_metricas_zeradas(resultado: dict[str, Any]) -> None:
    assert resultado["total_tarefas_analisadas"] == 0
    assert resultado["total_concluidas"] == 0
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0


def test_borda_lista_vazia_retorna_zeros_e_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        resultado = analyze_tasks([])
    _assert_metricas_zeradas(resultado)
    assert resultado["total_tarefas"] == 0
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_borda_apenas_pendentes_retorna_zeros() -> None:
    tarefas = [criar_tarefa(id="p1"), criar_tarefa(id="p2")]
    resultado = analyze_tasks(tarefas)
    _assert_metricas_zeradas(resultado)
    assert resultado["total_tarefas"] == 2
    assert resultado["total_pendentes"] == 2


def test_borda_canceladas_sao_ignoradas() -> None:
    cancelada = criar_tarefa(
        id="c1", status="CANCELADA", data_conclusao="2026-03-01T20:00:00"
    )
    _assert_metricas_zeradas(analyze_tasks([cancelada]))


def test_borda_concluida_sem_data_conclusao_e_ignorada() -> None:
    tarefa = criar_tarefa(id="c1", status="CONCLUIDA", data_conclusao=None)
    _assert_metricas_zeradas(analyze_tasks([tarefa]))


def test_borda_conclusao_igual_a_criacao_e_permitida() -> None:
    tarefa = criar_tarefa(
        id="c1", status="CONCLUIDA", data_conclusao="2026-03-01T08:00:00"
    )
    resultado = analyze_tasks([tarefa])
    assert resultado["total_concluidas"] == 1
    assert resultado["tempo_medio_conclusao_horas"] == 0.0


def test_borda_conclusao_exatamente_no_prazo_nao_e_atraso() -> None:
    tarefa = criar_tarefa(
        id="c1",
        status="CONCLUIDA",
        data_prazo="2026-03-01T12:00:00",
        data_conclusao="2026-03-01T12:00:00",
    )
    assert analyze_tasks([tarefa])["taxa_atraso_percentual"] == 0.0


def test_borda_arredondamento_em_duas_casas() -> None:
    tarefas = [
        criar_tarefa(id="a", prioridade="BAIXA", status="CONCLUIDA",
                     data_conclusao="2026-03-01T09:00:00"),
        criar_tarefa(id="b", prioridade="BAIXA", status="CONCLUIDA",
                     data_conclusao="2026-03-01T09:00:00"),
        criar_tarefa(id="c", prioridade="BAIXA", status="CONCLUIDA",
                     data_conclusao="2026-03-01T13:00:00"),
    ]
    resultado = analyze_tasks(tarefas)
    assert resultado["tempo_medio_conclusao_horas"] == 2.33
    assert resultado["taxa_atraso_percentual"] == 33.33
    baixa = resultado["metricas_por_prioridade"]["BAIXA"]
    assert baixa["tempo_medio_horas"] == 2.33


def test_borda_aceita_datetime_e_iso_com_z() -> None:
    tarefas = [
        criar_tarefa(
            id="dt",
            status="CONCLUIDA",
            data_criacao=datetime(2026, 3, 1, 8, tzinfo=timezone.utc),
            data_prazo=datetime(2026, 3, 1, 12, tzinfo=timezone.utc),
            data_conclusao=datetime(2026, 3, 1, 10, tzinfo=timezone.utc),
        ),
        criar_tarefa(
            id="iso",
            status="CONCLUIDA",
            data_criacao="2026-03-01T08:00:00Z",
            data_prazo="2026-03-01T12:00:00Z",
            data_conclusao="2026-03-01T12:00:00Z",
        ),
    ]
    assert analyze_tasks(tarefas)["tempo_medio_conclusao_horas"] == 3.0


# ---------------------------------------------------------------------------
# Validação do contrato de entrada
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("campos", "trecho_mensagem"),
    [
        ({"prioridade": "URGENTE"}, "Prioridade inválida"),
        ({"status": "EM_ANDAMENTO"}, "Status inválido"),
        ({"titulo": "ab"}, "titulo"),
        ({"titulo": "   "}, "titulo"),
        ({"id": ""}, "id"),
        ({"data_prazo": None}, "Campos obrigatórios ausentes"),
        ({"data_criacao": "01/03/2026"}, "ISO 8601"),
        ({"data_criacao": 20260301}, "ISO 8601"),
    ],
)
def test_contrato_entrada_invalida(
    campos: dict[str, Any], trecho_mensagem: str
) -> None:
    with pytest.raises(TaskValidationError, match=trecho_mensagem):
        analyze_tasks([criar_tarefa(**campos)])


def test_contrato_campo_ausente() -> None:
    tarefa = criar_tarefa()
    del tarefa["status"]
    with pytest.raises(TaskValidationError, match="status"):
        analyze_tasks([tarefa])


def test_contrato_id_duplicado() -> None:
    with pytest.raises(TaskValidationError, match="duplicado"):
        analyze_tasks([criar_tarefa(id="x"), criar_tarefa(id="x")])


@pytest.mark.parametrize(
    "entrada", [None, "tarefas", 42, [["nao", "e", "dict"]]]
)
def test_contrato_estrutura_de_entrada_invalida(entrada: Any) -> None:
    with pytest.raises(TaskValidationError):
        analyze_tasks(entrada)
