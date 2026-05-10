from dataclasses import dataclass


@dataclass
class Dosar:
    nr_dosar: str
    debitor: str
    nr_inregistrare: str
    tribunal: str
    data_inreg: str
    sectie: str = "SECȚIA A II A CIVILĂ"

    @property
    def case_uid(self):
        return f"{self.tribunal}|{self.nr_dosar}"