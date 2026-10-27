import json
import os
import threading

from config import DEFAULT_STAGES, EMS_EXTS, TECHNICIANS
from ems_parser import parse_job

EDITABLE_FIELDS = ("ro", "stage", "tech", "due")

def last_three_plate(value):
    plate = (value or "").strip()
    return plate[-3:] if plate else ""

class Board:
    def __init__(self, folder, state_path, auto_delete_date_out=False):
        self.folder = folder
        self.state_path = state_path
        self.auto_delete_date_out = auto_delete_date_out
        self.lock = threading.RLock()
        self.cache = {}
        self.state = {"techs": [], "stages": DEFAULT_STAGES[:], "jobs": {}}
        if os.path.exists(state_path):
            try:
                with open(state_path, encoding="utf-8") as f:
                    self.state.update(json.load(f))
            except Exception as e:
                print("Could not read", state_path, e)
        self.state["stages"] = DEFAULT_STAGES[:]     
        self.state["techs"] = TECHNICIANS[:]

    
    def save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
        os.replace(tmp, self.state_path)

    
    def stems(self):
        try:
            names = os.listdir(self.folder)
        except OSError:
            return {}
        out = {}
        for n in names:
            stem, ext = os.path.splitext(n)
            if ext.lower() in EMS_EXTS:
                out.setdefault(stem, []).append(n)
        return {s: f for s, f in out.items() if any(x.lower().endswith(".veh") for x in f)}

    def _signature(self, files):
        sig = []
        for f in sorted(files):
            p = os.path.join(self.folder, f)
            if os.path.exists(p):
                sig.append((f, os.path.getmtime(p), os.path.getsize(p)))
        return tuple(sig)

    def scan(self):
        with self.lock:
            found = self.stems()
            for stem, files in found.items():
                sig = self._signature(files)
                if self.cache.get(stem, (None,))[0] == sig:
                    continue
                try:
                    self.cache[stem] = (sig, parse_job(self.folder, stem))
                except Exception as e:     
                    self.cache[stem] = (None, {"error": str(e)})
            for stem in [s for s in self.cache if s not in found]:
                del self.cache[stem]
            gone = [s for s in self.state["jobs"] if s not in found]
            for s in gone:
                del self.state["jobs"][s]
            if gone:
                self.save()
            if self.auto_delete_date_out:
                for stem, (_, job) in list(self.cache.items()):
                    if job.get("date_out"):
                        self.deliver(stem)

    def snapshot(self):
        with self.lock:
            jobs = []
            for stem, (_, job) in self.cache.items():
                if "error" in job:
                    continue
                mine = self.state["jobs"].get(stem, {})
                jobs.append({
                    "id": stem,
                    "vehicle": job["vehicle"],
                    "plate": last_three_plate(job["plate"]),
                    "ro": mine.get("ro", ""),
                    "stage": mine.get("stage") or self.state["stages"][0],
                    "tech": mine.get("tech", ""),
                    "due": mine.get("due") or job["due"],
                })
            return {
                "jobs": jobs,
                "techs": self.state["techs"],
                "stages": self.state["stages"],
                "folder": self.folder,
            }


    def update(self, stem, field, value):
        with self.lock:
            if stem not in self.cache or field not in EDITABLE_FIELDS:
                raise KeyError("unknown job/field")
            self.state["jobs"].setdefault(stem, {})[field] = value
            self.save()

    def deliver(self, stem):
        with self.lock:
            failed = []
            for f in self.stems().get(stem, []):
                try:
                    os.remove(os.path.join(self.folder, f))
                except OSError as e:
                    failed.append(f"{f}: {e}")
            self.cache.pop(stem, None)
            self.state["jobs"].pop(stem, None)
            self.save()
            return failed
