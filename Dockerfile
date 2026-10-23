# Imagem de execução do Test Harness do TaskAnalyzer.
# Base leve e imutável: o resultado é o mesmo em qualquer máquina.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Usuário sem privilégios de administrador (princípio do menor privilégio).
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Dependências primeiro, para aproveitar o cache de camadas do Docker.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser tests/ tests/
RUN chown appuser:appuser /app

USER appuser

CMD ["pytest", "tests/test_harness.py", "-v"]
