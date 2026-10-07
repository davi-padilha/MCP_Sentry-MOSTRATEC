"""Mede tokens e tempos das revisões a partir dos rollouts do Codex.

O Codex grava cada conversa em ~/.codex/sessions/AAAA/MM/DD/rollout-*.jsonl.
Este script só lê esses arquivos e exporta CONTAGENS: nunca copia texto de
mensagens, argumentos de ferramentas, resultados, raciocínio ou instruções.

Por turno (cada pedido do usuário), registra:
  - tokens: entrada, entrada em cache, entrada sem cache, saída, raciocínio e total;
  - tempo da IA: duração do turno e tempo até o primeiro token;
  - tempo do operador: intervalo entre o fim do turno anterior e o início deste;
  - chamadas MCP: quantidade, ferramentas, erros e tamanho do resultado
    (o tamanho do resultado de sentry_review_current_block é o tamanho do dossiê).

Uso:
  py -3 medir_tokens_rollouts.py --desde 2026-10-05 --ate 2026-10-06 \
      --servidor-contem _teste --saida C:\\CAMINHO\\tokens
  py -3 medir_tokens_rollouts.py --mapa C:\\CAMINHO\\mapa.csv --saida C:\\CAMINHO\\tokens

O --mapa é um CSV com a coluna `sessao` (id da sessão ou nome do arquivo de
rollout) e colunas livres (por exemplo id, serie, versao, repeticao), que são
copiadas para as tabelas de saída.
"""
import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens", "total_tokens")


def text_length(content):
    """Soma o tamanho dos textos de um resultado MCP sem guardar o texto."""
    total = 0
    for item in content or []:
        if isinstance(item, dict):
            if isinstance(item.get("text"), str):
                total += len(item["text"])
            elif item.get("type") not in (None, "text"):
                total += len(json.dumps(item, ensure_ascii=False))
    return total


def empty_turn(turn_id):
    return {"turn_id": turn_id, "tokens": None, "total_ao_fim": None,
            "started_at": None, "completed_at": None, "duracao_ms": None,
            "primeiro_token_ms": None, "mcp_chamadas": 0, "mcp_erros": 0,
            "mcp_resultado_chars": 0, "mcp_ferramentas": [], "dossie_chars": 0,
            "model": None, "effort": None}


def read_rollout(path):
    """Lê um rollout e devolve metadados da sessão e a lista de turnos."""
    meta = {"arquivo": path.name, "sessao": "", "cwd": "", "cli_version": "", "inicio": "", "derivada": False}
    turns, order = {}, []
    thread_total = None
    # Tokens já acumulados antes do primeiro turno deste arquivo (conversa derivada).
    inherited = None
    count_total = None

    def turn(turn_id):
        if turn_id not in turns:
            turns[turn_id] = empty_turn(turn_id)
            order.append(turn_id)
        return turns[turn_id]

    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind, payload = event.get("type"), event.get("payload")
            if not isinstance(payload, dict):
                continue
            ptype = payload.get("type")
            if kind == "session_meta":
                meta.update(sessao=payload.get("id") or payload.get("session_id") or "",
                            cwd=payload.get("cwd") or "", cli_version=payload.get("cli_version") or "",
                            inicio=payload.get("timestamp") or "",
                            derivada=bool(payload.get("parent_thread_id")))
            elif kind == "turn_context" and payload.get("turn_id"):
                current = turn(payload["turn_id"])
                current["model"] = payload.get("model")
                current["effort"] = payload.get("effort")
            elif kind == "token_usage_record" and payload.get("turn_id"):
                # turn_token_usage é acumulado dentro do turno: vale o último registro.
                turn(payload["turn_id"])["tokens"] = payload.get("turn_token_usage") or payload.get("usage")
                thread_total = payload.get("thread_token_usage") or thread_total
            elif kind == "event_msg" and ptype == "task_started" and payload.get("turn_id"):
                turn(payload["turn_id"])["started_at"] = payload.get("started_at")
            elif kind == "event_msg" and ptype == "task_complete" and payload.get("turn_id"):
                current = turn(payload["turn_id"])
                current["started_at"] = current["started_at"] or payload.get("started_at")
                current["completed_at"] = payload.get("completed_at")
                current["duracao_ms"] = payload.get("duration_ms")
                current["primeiro_token_ms"] = payload.get("time_to_first_token_ms")
            elif kind == "event_msg" and ptype == "token_count" and order:
                # Alternativa para versões sem token_usage_record: o total acumulado
                # da conversa no fim de cada turno. A diferença entre turnos dá o
                # gasto do turno, sem contar duas vezes eventos repetidos.
                info = payload.get("info") or {}
                total = info.get("total_token_usage")
                if total:
                    if inherited is None:
                        last = info.get("last_token_usage") or {}
                        inherited = {f: int(total.get(f) or 0) - int(last.get(f) or 0) for f in TOKEN_FIELDS}
                    turns[order[-1]]["total_ao_fim"] = total
                    count_total = total
            elif kind == "event_msg" and ptype == "item_completed":
                item = payload.get("item") or {}
                if item.get("type") == "McpToolCall" and payload.get("turn_id"):
                    current = turn(payload["turn_id"])
                    result = item.get("result") or {}
                    size = text_length(result.get("content"))
                    current["mcp_chamadas"] += 1
                    current["mcp_erros"] += bool(result.get("isError")) or item.get("status") not in (None, "completed")
                    current["mcp_resultado_chars"] += size
                    tool = item.get("tool") or ""
                    current["mcp_ferramentas"].append(f"{item.get('server') or ''}.{tool}")
                    if tool == "sentry_review_current_block":
                        current["dossie_chars"] += size
    ordered = [turns[turn_id] for turn_id in order]
    previous = inherited or {field: 0 for field in TOKEN_FIELDS}
    for turn_data in ordered:
        if turn_data["tokens"] is None and turn_data["total_ao_fim"]:
            end = turn_data["total_ao_fim"]
            turn_data["tokens_delta"] = {f: int(end.get(f) or 0) - int(previous.get(f) or 0) for f in TOKEN_FIELDS}
        if turn_data["total_ao_fim"]:
            previous = turn_data["total_ao_fim"]
    meta["herdados"] = int((inherited or {}).get("total_tokens") or 0)
    return meta, ordered, thread_total or count_total


def tokens_of(turn_data):
    if turn_data["tokens"]:
        tokens, source = turn_data["tokens"], "turn_token_usage"
    elif turn_data.get("tokens_delta"):
        tokens, source = turn_data["tokens_delta"], "token_count_acumulado"
    else:
        tokens, source = {}, "ausente"
    row = {field: int(tokens.get(field) or 0) for field in TOKEN_FIELDS}
    row["input_sem_cache"] = row["input_tokens"] - row["cached_input_tokens"]
    # Valores negativos aparecem em formatos antigos (contador reiniciado);
    # marcar em vez de esconder, para não entrarem nas medianas por engano.
    row["fonte_tokens"] = "inconsistente" if any(value < 0 for value in row.values()) else source
    return row


def rollout_files(root, since, until):
    for path in sorted(root.rglob("rollout-*.jsonl")):
        try:
            year, month, day = (int(part) for part in path.parts[-4:-1])
            day_of_file = date(year, month, day)
        except ValueError:
            day_of_file = None
        if day_of_file and ((since and day_of_file < since) or (until and day_of_file > until)):
            continue
        yield path


def load_map(path):
    rows = {}
    for row in csv.DictReader(Path(path).open(encoding="utf-8")):
        key = (row.get("sessao") or "").strip()
        if key:
            rows[key] = {k: v for k, v in row.items() if k != "sessao"}
    return rows


def matches_map(meta, mapping):
    for key in (meta["sessao"], meta["arquivo"]):
        if key in mapping:
            return mapping[key]
    for key, extra in mapping.items():
        if key and key in meta["arquivo"]:
            return extra
    return None


def write_csv(path, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(field for row in rows for field in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(turn_rows):
    """Resumo por posição do turno (1 = tarefa, 2 = revisão, 3 = registro)."""
    by_position = defaultdict(list)
    for row in turn_rows:
        if row["fonte_tokens"] in ("inconsistente", "ausente"):
            continue
        by_position[row["turno"]].append(row)
    print("\n| Turno | n | Entrada (mediana) | Sem cache | Saída | Raciocínio | Dossiê (chars) | Duração IA (s) | Espera antes (s) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for position in sorted(by_position):
        group = by_position[position]
        def med(field, scale=1):
            values = [row[field] / scale for row in group if isinstance(row.get(field), (int, float))]
            return f"{statistics.median(values):,.0f}" if values else "NA"
        def med_s(field):
            values = [row[field] / 1000 for row in group if isinstance(row.get(field), (int, float))]
            return f"{statistics.median(values):.1f}" if values else "NA"
        dossier = [row["dossie_chars"] for row in group if row["dossie_chars"]]
        waits = [row["espera_antes_s"] for row in group if isinstance(row["espera_antes_s"], (int, float))]
        print(f"| {position} | {len(group)} | {med('input_tokens')} | {med('input_sem_cache')} | {med('output_tokens')} "
              f"| {med('reasoning_output_tokens')} | {f'{statistics.median(dossier):,.0f}' if dossier else 'NA'} "
              f"| {med_s('duracao_ms')} | {f'{statistics.median(waits):.0f}' if waits else 'NA'} |")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Tokens e tempos das revisões a partir dos rollouts do Codex")
    parser.add_argument("--sessoes", type=Path, default=Path.home() / ".codex" / "sessions")
    parser.add_argument("--desde", type=date.fromisoformat)
    parser.add_argument("--ate", type=date.fromisoformat)
    parser.add_argument("--cwd-contem", help="só sessões cujo cwd contém este texto (ex.: workspace-codex)")
    parser.add_argument("--servidor-contem", help="só sessões com chamada MCP a servidor cujo nome contém este texto")
    parser.add_argument("--mapa", help="CSV com coluna sessao e colunas livres (id, serie, versao, repeticao)")
    parser.add_argument("--saida", type=Path, required=True, help="pasta onde gravar sessoes.csv e turnos.csv")
    args = parser.parse_args(argv)

    mapping = load_map(args.mapa) if args.mapa else None
    session_rows, turn_rows, warnings = [], [], []
    for path in rollout_files(args.sessoes, args.desde, args.ate):
        meta, turns, thread_total = read_rollout(path)
        extra = {}
        if mapping is not None:
            extra = matches_map(meta, mapping)
            if extra is None:
                continue
        if args.cwd_contem and args.cwd_contem.lower() not in meta["cwd"].lower():
            continue
        servers = {tool.split(".", 1)[0] for t in turns for tool in t["mcp_ferramentas"]}
        if args.servidor_contem and not any(args.servidor_contem.lower() in s.lower() for s in servers):
            continue

        previous_end = None
        totals = defaultdict(int)
        for position, turn_data in enumerate(turns, 1):
            tokens = tokens_of(turn_data)
            for field, value in tokens.items():
                if isinstance(value, int):
                    totals[field] += value
            wait = (turn_data["started_at"] - previous_end
                    if turn_data["started_at"] is not None and previous_end is not None else "")
            previous_end = turn_data["completed_at"] or previous_end
            turn_rows.append({
                "sessao": meta["sessao"], **extra, "turno": position,
                "modelo": turn_data["model"] or "", "esforco": turn_data["effort"] or "",
                **tokens,
                "duracao_ms": turn_data["duracao_ms"] if turn_data["duracao_ms"] is not None else "",
                "primeiro_token_ms": turn_data["primeiro_token_ms"] if turn_data["primeiro_token_ms"] is not None else "",
                "espera_antes_s": wait,
                "mcp_chamadas": turn_data["mcp_chamadas"], "mcp_erros": turn_data["mcp_erros"],
                "mcp_resultado_chars": turn_data["mcp_resultado_chars"],
                "dossie_chars": turn_data["dossie_chars"],
                "mcp_ferramentas": ";".join(turn_data["mcp_ferramentas"]),
            })
        # O total da conversa inclui tokens herdados quando ela deriva de outra (fork).
        expected = totals["total_tokens"] + meta["herdados"]
        if thread_total and int(thread_total.get("total_tokens") or 0) != expected:
            warnings.append(f"{meta['arquivo']}: soma dos turnos + herdados ({expected}) difere do total da "
                            f"conversa ({thread_total.get('total_tokens')})")
        if mapping is not None and len(turns) != 3:
            warnings.append(f"{meta['arquivo']}: {len(turns)} turnos (o protocolo previa 3)")
        session_rows.append({"sessao": meta["sessao"], "arquivo": meta["arquivo"], **extra,
                             "inicio": meta["inicio"], "cli_version": meta["cli_version"],
                             "derivada": "sim" if meta["derivada"] else "nao", "tokens_herdados": meta["herdados"],
                             "turnos": len(turns), **dict(totals)})

    if mapping is not None:
        found = {row["sessao"] for row in session_rows} | {row["arquivo"] for row in session_rows}
        missing = [key for key in mapping if key not in found and not any(key in name for name in found)]
        if missing:
            warnings.append(f"{len(missing)} sessões do mapa não encontradas: {', '.join(missing[:5])}")

    args.saida.mkdir(parents=True, exist_ok=True)
    write_csv(args.saida / "sessoes.csv", session_rows)
    write_csv(args.saida / "turnos.csv", turn_rows)
    print(f"{len(session_rows)} sessões e {len(turn_rows)} turnos em {args.saida}")
    if turn_rows:
        summarize(turn_rows)
    for warning in warnings:
        print("aviso:", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
