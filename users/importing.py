"""CSV decoding and preview. No writes or HTTP dependencies."""

import csv
import io

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import User
from .validators import validate_cpf

NAME_HEADERS = {
    "nome",
    "name",
    "nome completo",
    "cliente",
    "comprador",
    "nome do comprador",
    "nome do cliente",
}


EMAIL_HEADERS = {"email", "e-mail", "email do comprador", "email do cliente"}


CPF_HEADERS = {"cpf", "documento", "cpf/cnpj", "documento do comprador"}


def _header(value):
    import unicodedata

    return "".join(
        c
        for c in unicodedata.normalize("NFKD", value.lower().strip())
        if not unicodedata.combining(c)
    )


def parse_student_csv(upload):
    raw = upload.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = {_header(h): h for h in (reader.fieldnames or [])}
    if {
        "pago_de",
        "pago_ate",
        "proximo_vencimento",
        "mensalidade",
        "renovacao_anterior",
    } & set(headers):
        raise ValueError(
            "Este arquivo contém períodos financeiros. Escolha Migração de mensalidades quitadas para preservar as datas de acesso."
        )

    def key(choices):
        return next(
            (headers.get(_header(c)) for c in choices if _header(c) in headers), None
        )

    name_key, email_key, cpf_key = (
        key(NAME_HEADERS),
        key(EMAIL_HEADERS),
        key(CPF_HEADERS),
    )
    if not email_key:
        raise ValueError("Coluna de e-mail ausente.")
    rows = []
    seen = set()
    for row in reader:
        if len(rows) >= 5000:
            break
        email = (row.get(email_key) or "").strip().lower()
        name = (row.get(name_key) or "").strip() if name_key else ""
        cpf = (row.get(cpf_key) or "").strip() if cpf_key else ""
        status = "Novo aluno"
        try:
            validate_email(email)
        except ValidationError:
            status = "E-mail inválido"
        if status == "E-mail inválido":
            pass
        elif email in seen:
            status = "E-mail repetido no arquivo"
        elif User.objects.filter(email__iexact=email, role=User.Role.STUDENT).exists():
            status = "Já cadastrado"
        elif User.objects.filter(email__iexact=email).exists():
            status = "E-mail já usado por outra conta"
        seen.add(email)
        if cpf:
            try:
                cpf = validate_cpf(cpf)
            except ValidationError:
                cpf = ""
        rows.append({"name": name, "email": email, "cpf": cpf, "status": status})
    return rows
