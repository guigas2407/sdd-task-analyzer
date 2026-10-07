"""Módulo TaskAnalyzer: métricas de produtividade sobre tarefas.

Implementa o contrato executável descrito em ``specs/task_analyzer_spec.md``.
O processamento ocorre estritamente em memória, sem persistência.

Example:
    >>> from src.task_analyzer import analyze_tasks
    >>> analyze_tasks([])["total_tarefas_analisadas"]
    0
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Final, NoReturn, TypedDict

logger: logging.Logger = logging.getLogger(__name__)

PRIORIDADES: Final[tuple[str, ...]] = ("BAIXA", "MEDIA", "ALTA")
STATUS_VALIDOS: Final[tuple[str, ...]] = ("PENDENTE", "CONCLUIDA", "CANCELADA")
CAMPOS_OBRIGATORIOS: Final[tuple[str, ...]] = (
    "id",
    "titulo",
    "prioridade",
    "data_criacao",
    "data_prazo",
    "status",
)
TAMANHO_MINIMO_TITULO: Final[int] = 3
SEGUNDOS_POR_HORA: Final[float] = 3600.0
CASAS_DECIMAIS: Final[int] = 2
MSG_DATA_INCONSISTENTE: Final[str] = (
    "Data de conclusão não pode ser anterior à data de criação da tarefa."
)


class TaskValidationError(ValueError):
    """Erro de validação de uma tarefa de entrada.

    Herda de ``ValueError`` para manter compatibilidade com a regra de
    negócio 2 da especificação (Fase 1), que exige um ``ValueError``.
    """


class MetricasPrioridade(TypedDict):
    """Métricas calculadas para um nível de prioridade."""

    total: int
    tempo_medio_horas: float
    taxa_atraso_percentual: float


class ResultadoAnalise(TypedDict):
    """Dicionário de retorno de :func:`analyze_tasks`."""

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    total_tarefas_analisadas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    metricas_por_prioridade: dict[str, MetricasPrioridade]


@dataclass(frozen=True, slots=True)
class _TarefaValidada:
    """Tarefa já validada, com datas convertidas para ``datetime`` UTC."""

    id: str
    prioridade: str
    status: str
    data_criacao: datetime
    data_prazo: datetime
    data_conclusao: datetime | None


@dataclass(frozen=True, slots=True)
class _Conclusao:
    """Dados de uma tarefa concluída necessários para as métricas."""

    prioridade: str
    duracao_horas: float
    atrasada: bool


def _falhar(mensagem: str, tarefa_id: object) -> NoReturn:
    """Registra o erro em log e dispara ``TaskValidationError``.

    Args:
        mensagem: Descrição do problema encontrado.
        tarefa_id: Identificador da tarefa inválida (pode ser ``None``).

    Raises:
        TaskValidationError: Sempre.
    """
    logger.error(
        "evento=validacao_falhou tarefa_id=%s motivo=%s", tarefa_id, mensagem
    )
    raise TaskValidationError(mensagem)


def _converter_data(valor: object, campo: str, tarefa_id: object) -> datetime:
    """Converte um valor de data para ``datetime`` com fuso horário.

    Datas sem fuso horário são interpretadas como UTC.

    Args:
        valor: ``datetime`` ou string no formato ISO 8601.
        campo: Nome do campo, usado na mensagem de erro.
        tarefa_id: Identificador da tarefa, usado no log.

    Returns:
        A data convertida, sempre com ``tzinfo`` definido.

    Raises:
        TaskValidationError: Se o valor não for uma data ISO 8601 válida.
    """
    if isinstance(valor, datetime):
        data = valor
    elif isinstance(valor, str):
        try:
            data = datetime.fromisoformat(valor)
        except ValueError:
            _falhar(
                f"Campo '{campo}' não está no formato ISO 8601.", tarefa_id
            )
    else:
        _falhar(
            f"Campo '{campo}' deve ser datetime ou string ISO 8601.", tarefa_id
        )
    if data.tzinfo is None:
        return data.replace(tzinfo=timezone.utc)
    return data


def _validar_campos_obrigatorios(
    tarefa: Mapping[str, Any], tarefa_id: object
) -> None:
    """Garante que todos os campos obrigatórios estão presentes e não nulos.

    Args:
        tarefa: Registro de entrada.
        tarefa_id: Identificador da tarefa, usado no log.

    Raises:
        TaskValidationError: Se algum campo obrigatório estiver ausente.
    """
    ausentes = [c for c in CAMPOS_OBRIGATORIOS if tarefa.get(c) is None]
    if ausentes:
        _falhar(
            f"Campos obrigatórios ausentes: {', '.join(ausentes)}.", tarefa_id
        )


def _validar_textos(tarefa: Mapping[str, Any], tarefa_id: object) -> None:
    """Valida ``id``, ``titulo``, ``prioridade`` e ``status``.

    Args:
        tarefa: Registro de entrada com os campos obrigatórios presentes.
        tarefa_id: Identificador da tarefa, usado no log.

    Raises:
        TaskValidationError: Se algum valor violar as restrições do contrato.
    """
    if not isinstance(tarefa["id"], str) or not tarefa["id"].strip():
        _falhar("Campo 'id' deve ser uma string não vazia.", tarefa_id)
    titulo = tarefa["titulo"]
    minimo = TAMANHO_MINIMO_TITULO
    if not isinstance(titulo, str) or len(titulo.strip()) < minimo:
        _falhar(
            f"Campo 'titulo' deve ter no mínimo {minimo} caracteres.",
            tarefa_id,
        )
    if tarefa["prioridade"] not in PRIORIDADES:
        _falhar(f"Prioridade inválida: {tarefa['prioridade']!r}.", tarefa_id)
    if tarefa["status"] not in STATUS_VALIDOS:
        _falhar(f"Status inválido: {tarefa['status']!r}.", tarefa_id)


def _validar_tarefa(tarefa: object) -> _TarefaValidada:
    """Valida um registro de entrada e o converte em ``_TarefaValidada``.

    Args:
        tarefa: Registro de entrada (esperado: dicionário).

    Returns:
        A tarefa validada.

    Raises:
        TaskValidationError: Se o registro violar o contrato de entrada ou a
            invariante temporal (conclusão anterior à criação).
    """
    if not isinstance(tarefa, Mapping):
        _falhar("Cada tarefa deve ser um dicionário.", None)
    tarefa_id = tarefa.get("id")
    _validar_campos_obrigatorios(tarefa, tarefa_id)
    _validar_textos(tarefa, tarefa_id)
    data_criacao = _converter_data(
        tarefa["data_criacao"], "data_criacao", tarefa_id
    )
    data_prazo = _converter_data(
        tarefa["data_prazo"], "data_prazo", tarefa_id
    )
    valor_conclusao = tarefa.get("data_conclusao")
    data_conclusao = (
        None
        if valor_conclusao is None
        else _converter_data(valor_conclusao, "data_conclusao", tarefa_id)
    )
    if data_conclusao is not None and data_conclusao < data_criacao:
        _falhar(MSG_DATA_INCONSISTENTE, tarefa_id)
    return _TarefaValidada(
        id=tarefa["id"],
        prioridade=tarefa["prioridade"],
        status=tarefa["status"],
        data_criacao=data_criacao,
        data_prazo=data_prazo,
        data_conclusao=data_conclusao,
    )


def _validar_tarefas(tarefas: object) -> list[_TarefaValidada]:
    """Valida a lista de entrada completa, incluindo unicidade dos ``id``.

    Args:
        tarefas: Lista (ou outra sequência) de registros de tarefa.

    Returns:
        Lista de tarefas validadas, na mesma ordem da entrada.

    Raises:
        TaskValidationError: Se a entrada não for uma sequência, se algum
            registro for inválido ou se houver ``id`` duplicado.
    """
    if isinstance(tarefas, (str, bytes)) or not isinstance(tarefas, Sequence):
        _falhar("A entrada deve ser uma lista de tarefas.", None)
    validadas: list[_TarefaValidada] = []
    ids_vistos: set[str] = set()
    for tarefa in tarefas:
        validada = _validar_tarefa(tarefa)
        if validada.id in ids_vistos:
            _falhar(f"Id de tarefa duplicado: {validada.id!r}.", validada.id)
        ids_vistos.add(validada.id)
        validadas.append(validada)
    return validadas


def _extrair_conclusoes(
    tarefas: Sequence[_TarefaValidada],
) -> list[_Conclusao]:
    """Seleciona as tarefas elegíveis (``CONCLUIDA`` com data de conclusão).

    Args:
        tarefas: Tarefas já validadas.

    Returns:
        Duração em horas e indicador de atraso de cada tarefa elegível.
    """
    return [
        _Conclusao(
            prioridade=tarefa.prioridade,
            duracao_horas=(
                tarefa.data_conclusao - tarefa.data_criacao
            ).total_seconds()
            / SEGUNDOS_POR_HORA,
            atrasada=tarefa.data_conclusao > tarefa.data_prazo,
        )
        for tarefa in tarefas
        if tarefa.status == "CONCLUIDA" and tarefa.data_conclusao is not None
    ]


def _media_horas(conclusoes: Sequence[_Conclusao]) -> float:
    """Calcula a duração média em horas, sem risco de divisão por zero.

    Args:
        conclusoes: Tarefas concluídas elegíveis.

    Returns:
        Média arredondada em 2 casas decimais, ou ``0.0`` se não houver
        itens.
    """
    if not conclusoes:
        return 0.0
    soma = sum(conclusao.duracao_horas for conclusao in conclusoes)
    return round(soma / len(conclusoes), CASAS_DECIMAIS)


def _taxa_atraso(conclusoes: Sequence[_Conclusao]) -> float:
    """Calcula o percentual de tarefas concluídas após o prazo.

    Args:
        conclusoes: Tarefas concluídas elegíveis.

    Returns:
        Percentual (0.0 a 100.0) arredondado em 2 casas decimais, ou ``0.0``
        se não houver itens.
    """
    if not conclusoes:
        return 0.0
    atrasadas = sum(1 for conclusao in conclusoes if conclusao.atrasada)
    return round(atrasadas * 100.0 / len(conclusoes), CASAS_DECIMAIS)


def _metricas_por_prioridade(
    conclusoes: Sequence[_Conclusao],
) -> dict[str, MetricasPrioridade]:
    """Agrupa as métricas pelas prioridades ``BAIXA``, ``MEDIA`` e ``ALTA``.

    Args:
        conclusoes: Tarefas concluídas elegíveis.

    Returns:
        Dicionário com as três prioridades, sempre presentes.
    """
    metricas: dict[str, MetricasPrioridade] = {}
    for prioridade in PRIORIDADES:
        grupo = [c for c in conclusoes if c.prioridade == prioridade]
        metricas[prioridade] = {
            "total": len(grupo),
            "tempo_medio_horas": _media_horas(grupo),
            "taxa_atraso_percentual": _taxa_atraso(grupo),
        }
    return metricas


def analyze_tasks(tarefas: Sequence[Mapping[str, Any]]) -> ResultadoAnalise:
    """Calcula as métricas de produtividade de uma lista de tarefas.

    Apenas tarefas com status ``CONCLUIDA`` e ``data_conclusao`` preenchida
    entram nas médias e taxas. Uma lista sem tarefas elegíveis retorna
    métricas zeradas e registra um ``logging.warning``.

    Args:
        tarefas: Registros de tarefa no formato do contrato de entrada.

    Returns:
        Dicionário com totais, tempo médio, taxa de atraso e métricas por
        prioridade.

    Raises:
        TaskValidationError: Se algum registro violar o contrato, inclusive
            quando ``data_conclusao`` for anterior a ``data_criacao``.
    """
    validadas = _validar_tarefas(tarefas)
    conclusoes = _extrair_conclusoes(validadas)
    if not conclusoes:
        logger.warning(
            "evento=sem_tarefas_concluidas total_tarefas=%d", len(validadas)
        )
    resultado: ResultadoAnalise = {
        "total_tarefas": len(validadas),
        "total_concluidas": len(conclusoes),
        "total_pendentes": sum(1 for t in validadas if t.status == "PENDENTE"),
        "total_tarefas_analisadas": len(conclusoes),
        "tempo_medio_conclusao_horas": _media_horas(conclusoes),
        "taxa_atraso_percentual": _taxa_atraso(conclusoes),
        "metricas_por_prioridade": _metricas_por_prioridade(conclusoes),
    }
    logger.info(
        "evento=analise_concluida total_tarefas=%d total_concluidas=%d",
        resultado["total_tarefas"],
        resultado["total_concluidas"],
    )
    return resultado


class TaskAnalyzer:
    """Fachada que preserva a assinatura pública definida na Fase 1."""

    @staticmethod
    def calcular_metricas(
        tarefas: Sequence[Mapping[str, Any]],
    ) -> ResultadoAnalise:
        """Alias de :func:`analyze_tasks` mantido pelo contrato da Fase 1.

        Args:
            tarefas: Registros de tarefa no formato do contrato de entrada.

        Returns:
            O mesmo resultado de :func:`analyze_tasks`.

        Raises:
            TaskValidationError: Nas mesmas condições de
                :func:`analyze_tasks`.
        """
        return analyze_tasks(tarefas)
