from dataclasses import dataclass


@dataclass
class Dosar:
    case_uid: str
    nr_dosar: str
    debitor: str
    nr_inregistrare: str
    tribunal: str
    data_inreg: str
    sectie: str | None = None