#!/usr/bin/env bash
# Commita os marts (data/marts/*.parquet) gerados pelo pipeline agendado.
#
# - Marts mudaram: commit citando o último relatório da Fenabrave.
# - Nada mudou: não commita (os Parquet são determinísticos, então "nada mudou" é
#   confiável), exceto se o último commit tiver 45 dias ou mais. Nesse caso grava a
#   data da verificação em data/marts/_ultima_verificacao.txt e commita, para o GitHub
#   não desativar o agendamento (ele desativa após 60 dias sem atividade no repositório).
set -euo pipefail

DIAS_PARA_MANTER_ATIVO=45

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

resumo=$(python -c "
import duckdb
mes, total = duckdb.sql(\"select strftime(ultimo_mes, '%m/%Y'), emplacamentos_ultimo_mes from 'data/marts/mart_emplacamentos_resumo.parquet'\").fetchall()[0]
print(f'{mes} ({total:,} emplacamentos de leves)'.replace(',', '.'))
")

git add data/marts/*.parquet

if ! git diff --cached --quiet; then
    mensagem="Atualiza marts até o relatório da Fenabrave de ${resumo}"
else
    ultimo_commit=$(git log -1 --format=%ct)
    dias=$(( ( $(date +%s) - ultimo_commit ) / 86400 ))
    if (( dias < DIAS_PARA_MANTER_ATIVO )); then
        echo "Marts sem mudança e último commit há ${dias} dia(s): nada a commitar."
        exit 0
    fi
    date -u +"%Y-%m-%dT%H:%M:%SZ" > data/marts/_ultima_verificacao.txt
    git add data/marts/_ultima_verificacao.txt
    mensagem="Registra verificação semanal (sem relatório novo há ${dias} dias; mantém o agendamento ativo)"
fi

git commit -m "${mensagem}"
# Alguém pode ter enviado commits durante a execução: traz antes de enviar
git pull --rebase --quiet origin "$(git rev-parse --abbrev-ref HEAD)"
git push
echo "Commit feito: ${mensagem}"
