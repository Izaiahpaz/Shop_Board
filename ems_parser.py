import os
import re

from config import MAKES
from dbf import read_dbf


def ymd(s):
    s = (s or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:]}" if re.fullmatch(r"\d{8}", s) else ""


def year4(y):
    y = (y or "").strip()
    if re.fullmatch(r"\d{4}", y):
        return y
    if re.fullmatch(r"\d{2}", y):
        return str(2000 + int(y) if int(y) <= 50 else 1900 + int(y))
    return ""


def parse_job(folder, stem):
    path = lambda ext: os.path.join(folder, stem + ext)

    veh = read_dbf(path(".veh"))[0]
    make = veh.get("V_MAKEDESC") or MAKES.get(veh.get("V_MAKECODE", ""),
                                              veh.get("V_MAKECODE", "").title())
    vehicle = " ".join(x for x in (year4(veh.get("V_MODEL_YR")), make, veh.get("V_MODEL")) if x)

    due = date_out = ""
    if os.path.exists(path(".ad2")):
        ad2 = read_dbf(path(".ad2"))[0]
        due = ymd(ad2.get("TAR_DATE"))
        date_out = ymd(ad2.get("DATE_OUT"))    

    return {"vehicle": vehicle, "plate": veh.get("PLATE_NO", ""),
            "due": due, "date_out": date_out}
