FROM python:3.13-slim
WORKDIR /app
COPY vault_backup_engine ./vault_backup_engine
RUN useradd --uid 10001 --create-home runner
USER runner
WORKDIR /workspace
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "vault_backup_engine"]
CMD ["--help"]
