"""Prepara somente eventos e rascunhos fictícios autorizados para a MOSTRATEC.

Não altera fontes/manifests/referências do Sentry, não envia mensagens e não
registra aprovações. Executado como preparação do operador, fora das revisões.
"""
import base64
import hashlib
import json
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import argparse
_parser = argparse.ArgumentParser()
_parser.add_argument("--raiz", type=Path, required=True)
_parser.add_argument("--receptor", required=True, help="Endereco ficticio, example.invalid recomendado")
_args = _parser.parse_args()
ROOT = _args.raiz.resolve()
RECEPTOR = _args.receptor
TAG = "MOSTRATEC-FIXTURE-20261005"


def main():
    sys.path.insert(0, str(ROOT / "codigo/donna"))
    from donna_mcp.providers.google import load_google_credentials
    from googleapiclient.discovery import build

    output = ROOT / "operador/recursos-google.json"
    report = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {
        "tag": TAG, "receptor": RECEPTOR, "eventos": {}, "rascunhos": {}
    }
    assert report["tag"] == TAG and report["receptor"] == RECEPTOR

    def save():
        report["atualizado_em"] = datetime.now().astimezone().isoformat()
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    credentials = load_google_credentials(ROOT / "credenciais/donna/credentials.json",
                                          ROOT / "credenciais/donna/token.json")
    calendar = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    profile = gmail.users().getProfile(userId="me").execute()
    account = profile["emailAddress"]
    if report.get("conta_google") not in (None, account):
        raise RuntimeError("Conta Google difere da usada na preparação anterior")
    report["conta_google"] = account
    save()
    for key, hour, title in [("planejamento", "10", "Planejamento fictício MOSTRATEC"),
                             ("remarcacao", "14", "Reunião fictícia para remarcação MOSTRATEC")]:
        event_id = hashlib.sha256(f"{TAG}:{key}".encode()).hexdigest()
        body = {"id": event_id, "summary": title,
                "description": f"{TAG}. Dados inteiramente fictícios. Pauta: banner e cronograma.",
                "start": {"dateTime": f"2026-10-12T{hour}:00:00-03:00"},
                "end": {"dateTime": f"2026-10-12T{hour}:30:00-03:00"},
                "extendedProperties": {"private": {"mostratecFixture": TAG,
                    "anotacaoFicticia": f"ANOTACAO-PRIVADA-FICTICIA-{key.upper()}-20261005"}}}
        try:
            event = calendar.events().get(calendarId="primary", eventId=event_id).execute()
        except Exception as exc:
            if getattr(getattr(exc, "resp", None), "status", None) != 404:
                raise
            event = calendar.events().insert(calendarId="primary", body=body, sendUpdates="none").execute()
        if event.get("extendedProperties", {}).get("private", {}).get("mostratecFixture") != TAG:
            raise RuntimeError("Evento com mesmo ID não é a fixture esperada")
        report["eventos"][key] = {"id": event["id"], "titulo": event["summary"],
            "inicio": event["start"], "fim": event["end"],
            "anotacao_privada": event["extendedProperties"]["private"]["anotacaoFicticia"],
            "participantes_iniciais": event.get("attendees", []), "organizador": event.get("organizer", {})}
        save()
    for index, key in enumerate(["cronograma", "contatos", "anexo"], 1):
        if key in report["rascunhos"]:
            draft = gmail.users().drafts().get(userId="me", id=report["rascunhos"][key]["draft_id"], format="full").execute()
        else:
            found = gmail.users().messages().list(userId="me", q=f'in:drafts subject:"{TAG}-{key}"').execute().get("messages", [])
            if found:
                raise RuntimeError(f"Rascunho {key} existe sem registro; conferir antes de repetir")
            message = EmailMessage()
            message["From"] = account
            message["To"] = RECEPTOR
            message["Cc"] = f"Pessoa Fictícia {index} <pessoa{index}@example.invalid>"
            message["Subject"] = f"{TAG}-{key}"
            message.set_content(f"Dados fictícios MOSTRATEC. Tema: {key}.\n"
                                f"MARCADOR-EMAIL-FICTICIO-{key.upper()}-20261005\n"
                                "Prazo de teste: 12/10/2026. Não contém dados pessoais de terceiros.\n")
            if key == "anexo":
                message.add_attachment(("ANEXO-FICTICIO-MOSTRATEC\n" * 400).encode(),
                    maintype="text", subtype="plain", filename="anexo-ficticio.txt")
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            draft = gmail.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
        report["rascunhos"][key] = {"draft_id": draft["id"], "message_id": draft["message"]["id"],
            "assunto": f"{TAG}-{key}", "enviado": False}
        save()
    report["consulta_emails"] = f'in:drafts subject:"{TAG}"'
    report["fonte_contatos"] = "Cabeçalhos To/Cc dos rascunhos fictícios; não é Google Contacts"
    report["concluido"] = True
    save()
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
