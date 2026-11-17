"""Explicit CSV contract for migration of paid monthly course periods."""

import csv
import io
from datetime import timedelta
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from courses.models import Course
from users.models import User


class MigrationRowForm(forms.Form):
    nome = forms.CharField(max_length=255)
    email = forms.EmailField(max_length=254)
    curso = forms.SlugField(max_length=50)
    pago_de = forms.DateField(input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    pago_ate = forms.DateField(input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    proximo_vencimento = forms.DateField(input_formats=["%Y-%m-%d", "%d/%m/%Y"])
    mensalidade = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    plataforma = forms.ChoiceField(
        choices=[("eduzz", "Eduzz"), ("hotmart", "Hotmart"), ("other", "Outra")]
    )
    assinatura_anterior = forms.CharField(max_length=100, required=False)
    renovacao_anterior = forms.ChoiceField(
        choices=[
            ("pendente", "A conferir"),
            ("ativa", "Ativa"),
            ("encerrada", "Encerramento informado"),
        ]
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def clean(self):
        data = super().clean()
        start, end, due = (
            data.get(k) for k in ["pago_de", "pago_ate", "proximo_vencimento"]
        )
        if start and end and end < start:
            raise ValidationError("O fim quitado não pode anteceder o início.")
        if end and due:
            try:
                expected = end + timedelta(days=1)
            except OverflowError:
                raise ValidationError("Data final fora do intervalo permitido.")
            if due != expected:
                raise ValidationError(
                    "O próximo vencimento deve ser o dia seguinte ao último dia quitado."
                )
        return data


def validate_migration_row(row):
    form = MigrationRowForm(row)
    if not form.is_valid():
        raise ValidationError(
            [
                f"{key}: {error}"
                for key, errors in form.errors.items()
                for error in errors
            ]
        )
    data = form.cleaned_data
    data["mensalidade"] = data["mensalidade"].quantize(Decimal("0.01"))
    if not Course.objects.filter(slug=data["curso"]).exists():
        raise ValidationError(
            "Curso não encontrado. Use o identificador exibido no painel."
        )
    users = User.objects.filter(email__iexact=data["email"])
    if users.count() > 1 or users.exclude(role=User.Role.STUDENT).exists():
        raise ValidationError(
            "E-mail ambíguo ou pertencente a uma conta que não é de aluno."
        )
    return data


def parse_subscription_csv(upload):
    raw = upload.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("O CSV deve ter no máximo 5 MB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = [h.strip().lower() for h in reader.fieldnames or []]
    if len(headers) != len(set(headers)):
        raise ValueError("Há colunas repetidas no arquivo.")
    required = set(MigrationRowForm.base_fields) - {"assinatura_anterior"}
    if not required.issubset(headers):
        raise ValueError(
            "Colunas ausentes: " + ", ".join(sorted(required - set(headers)))
        )
    rows, seen = [], {}
    for index, source in enumerate(reader, 2):
        if len(rows) >= 5000:
            raise ValueError("O CSV deve ter no máximo 5000 linhas.")
        if None in source:
            raise ValueError(f"Linha {index} possui mais campos que o cabeçalho.")
        row = {k.strip().lower(): (v or "").strip() for k, v in source.items()}
        row.update(valid=True, line=index)
        try:
            data = validate_migration_row(row)
            key = (data["email"], data["curso"])
            if key in seen:
                rows[seen[key]]["valid"] = False
                rows[seen[key]]["status"] = (
                    "Aluno/curso repetido no arquivo. Corrija todas as linhas desse vínculo."
                )
                raise ValidationError("Aluno/curso repetido no arquivo.")
            seen[key] = len(rows)
            row.update(
                {
                    k: v.isoformat() if hasattr(v, "isoformat") else str(v)
                    for k, v in data.items()
                }
            )
            row["status"] = "Período pronto para importar"
        except ValidationError as exc:
            row["valid"] = False
            row["status"] = " ".join(exc.messages)
        rows.append(row)
    if not rows:
        raise ValueError("O arquivo não contém alunos.")
    return rows
