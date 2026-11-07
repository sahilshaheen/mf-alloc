"""Read every sheet of an Excel file into plain row lists, whatever its true format.

AMCs name files .xls but ship xlsx (Nippon, Motilal) or, rarely, real OLE .xls (Aditya Birla).
The format is sniffed from the file's magic bytes, never from its extension.
"""

from __future__ import annotations

import io
from pathlib import Path

import openpyxl
import xlrd

_OLE = b"\xd0\xcf\x11\xe0"


def read_sheets(path: Path) -> dict[str, list[list]]:
    raw = path.read_bytes()
    if raw[:4] == _OLE:
        wb = xlrd.open_workbook(file_contents=raw)
        return {
            sh.name: [
                [None if c == "" else c for c in sh.row_values(i)]
                for i in range(sh.nrows)
            ]
            for sh in wb.sheets()
        }
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    return {
        n: [list(r) for r in wb[n].iter_rows(values_only=True)] for n in wb.sheetnames
    }
