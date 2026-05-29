import re

DOSAR_REGEX = r"^\d+\/\d+\/\d{4}"


class ValidationError(Exception):
    pass


def valideaza_dosar(dosar):
    if not re.match(DOSAR_REGEX, dosar.nr_dosar):
        raise ValidationError(f"Numar dosar invalid: {dosar.nr_dosar}")

    if len(dosar.debitor.strip()) < 3:
        raise ValidationError("Debitor invalid")

    if "@" in dosar.debitor:
        raise ValidationError("Debitor suspect")

    return True