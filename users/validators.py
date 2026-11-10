"""Validação de CPF (dígitos verificadores). Guardar sempre só os 11 dígitos."""
from django.core.exceptions import ValidationError


def only_digits(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def validate_cpf(value):
    digits = only_digits(value)
    if len(digits) != 11 or digits == digits[0] * 11:
        raise ValidationError("CPF inválido. Confira os números.", code="invalid_cpf")
    for size in (9, 10):
        total = sum(int(digits[i]) * (size + 1 - i) for i in range(size))
        check = (total * 10) % 11 % 10
        if check != int(digits[size]):
            raise ValidationError("CPF inválido. Confira os números.", code="invalid_cpf")
    return digits
