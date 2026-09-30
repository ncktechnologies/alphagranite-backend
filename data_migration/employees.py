"""Link Caspio employee references to Odyssey users.

Caspio refers to people three ways:
  - shop clock numbers (Shop_Data.shop_employee, Fab_Status.cut_by/edging_by/...)
  - full names (Fab_Status.*_employee_scheduled)
  - small per-list IDs (Fab_Status.template_by -> Employees_Template,
    sales IDs -> Active_Sales_Employees), which only carry a first name.

Every reference is first turned into a Caspio person (clock number + full name)
using Employees_Shop, Alpha_Employees and ProductionPerPerson, then matched to
an Odyssey user:
  1. users.hcp_employee_id == ClockNum AND the names agree   -> "hcp_id"
  2. otherwise a unique first + last name match               -> "name"
Clock numbers have been reused (e.g. Caspio 532 = Fernando Valencia-Lujano,
HCP 532 = Antonio Garcia), so an ID match whose names disagree is never used on
its own; it is reported as a conflict.
"""
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher

# Short names used in Caspio lists -> given name in Odyssey.
NICKNAMES = {"gabe": "gabriel"}


def _tokens(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"\(([^)]*)\)", r" \1 ", text.lower())  # "Dionissios (Denis)"
    return [t for t in re.split(r"[^a-z]+", text) if t]


def _similar(a, b):
    return a == b or (min(len(a), len(b)) >= 4 and SequenceMatcher(None, a, b).ratio() >= 0.8)


def _first_matches(caspio_first, user_first):
    for c in caspio_first:
        for name in {c, NICKNAMES.get(c, c)}:
            if any(_similar(name, u) for u in user_first):
                return True
    return False


def _last_matches(caspio_last, user_last):
    return any(_similar(c, u) for c in caspio_last for u in user_last)


def _norm_clock(value):
    value = (value or "").strip()
    if not value.isdigit():
        return None
    value = value.lstrip("0")
    return value or None


class Person:
    def __init__(self, clock, first, last):
        self.clock = clock
        self.first = _tokens(first)
        self.last = _tokens(last)

    @property
    def name(self):
        return " ".join(self.first + self.last).title()


class EmployeeDirectory:
    def __init__(self, tables, users):
        """tables: Caspio CSVs by name; users: (id, first_name, last_name, hcp_employee_id)."""
        self.by_clock = {}
        for r in tables.get("ProductionPerPerson", []):
            clock, name = _norm_clock(r.get("ClockNum")), (r.get("Name") or "").strip()
            if clock and name and clock not in self.by_clock:
                last, _, first = name.partition(",")  # "Vences, Freddy"
                self.by_clock[clock] = Person(clock, first, last)
        for table in ("Alpha_Employees", "Employees_Shop"):  # later lists win
            for r in tables.get(table, []):
                clock = _norm_clock(r.get("ClockNum"))
                if clock:
                    self.by_clock[clock] = Person(clock, r.get("FirstName"), r.get("LastName"))

        self.office_lists = {
            "template": {r["template_employee_id"].strip(): r["template_employee_name"].strip()
                         for r in tables.get("Employees_Template", [])
                         if (r.get("template_employee_id") or "").strip()},
            "sales": {r["sales_employee_id"].strip(): r["sales_employee_name"].strip()
                      for r in tables.get("Active_Sales_Employees", [])
                      if (r.get("sales_employee_id") or "").strip()},
        }

        self.users = [(uid, _tokens(first), _tokens(last)) for uid, first, last, _ in users]
        self.users_by_hcp = defaultdict(list)
        for (uid, first, last), (_, _, _, hcp) in zip(self.users, users):
            clock = _norm_clock(hcp)
            if clock:
                self.users_by_hcp[clock].append((uid, first, last))

        self.stats = defaultdict(Counter)       # field -> method -> rows
        self.unresolved = defaultdict(Counter)  # field -> "raw (name)" -> rows
        self.conflicts = {}                     # clock -> (caspio name, odyssey user ids)
        self._cache = {}

    # -- Caspio reference -> Caspio person ------------------------------
    def _person_from_name(self, full_name):
        tokens = _tokens(full_name)
        if not tokens:
            return None
        first, rest = tokens[:1], tokens[1:]
        hits = [p for p in self.by_clock.values()
                if _first_matches(first, p.first) and _last_matches(rest, p.last)]
        if len(hits) == 1:
            return hits[0]
        return Person(None, first[0], " ".join(rest))

    def _person_from_first_name(self, first_name):
        tokens = _tokens(first_name)
        if not tokens:
            return None
        hits = {}  # one person can hold several clock numbers (Eddie Uriostegui)
        for p in self.by_clock.values():
            if _first_matches(tokens, p.first):
                hits.setdefault(p.name, []).append(p)
        if len(hits) == 1:
            people = next(iter(hits.values()))
            # Prefer the clock number that is also this person's HCP id.
            return next((p for p in people if p.clock in self.users_by_hcp), people[0])
        return Person(None, first_name, "")

    # -- Caspio person -> Odyssey user -----------------------------------
    def _user_for(self, person):
        if person is None:
            return None, "unresolved"
        if person.clock:
            candidates = self.users_by_hcp.get(person.clock, [])
            agreeing = [uid for uid, _, last in candidates if _last_matches(person.last, last)]
            if len(agreeing) == 1:
                return agreeing[0], "hcp_id"
            if candidates and not agreeing and person.last:
                self.conflicts[person.clock] = (person.name, [uid for uid, _, _ in candidates])
        if person.first and person.last:
            by_name = [uid for uid, first, last in self.users
                       if _first_matches(person.first, first) and _last_matches(person.last, last)]
            if len(by_name) == 1:
                return by_name[0], "name"
        return None, "unresolved"

    def _user_for_first_name_only(self, person):
        """Office lists give only a first name; accept it if one user has it."""
        if person is None or person.last:
            return None, "unresolved"
        by_first = [uid for uid, first, _ in self.users if _first_matches(person.first, first)]
        return (by_first[0], "first_name") if len(by_first) == 1 else (None, "unresolved")

    def _resolve(self, field, key, raw, make_person, first_name_only=False):
        if key not in self._cache:
            person = make_person()
            uid, method = self._user_for(person)
            if uid is None and first_name_only:
                uid, method = self._user_for_first_name_only(person)
            self._cache[key] = (uid, method, person.name if person else "")
        uid, method, name = self._cache[key]
        self.stats[field][method] += 1
        if uid is None:
            self.unresolved[field][f"{raw} ({name})" if name and name != raw else raw] += 1
        return uid

    def by_clock_number(self, field, raw):
        clock = _norm_clock(raw)
        if not clock:
            return None
        return self._resolve(field, ("clock", clock), raw.strip(),
                             lambda: self.by_clock.get(clock) or Person(clock, "", ""))

    def by_name(self, field, raw):
        name = (raw or "").strip()
        if not name:
            return None
        return self._resolve(field, ("name", name.lower()), name,
                             lambda: self._person_from_name(name))

    def by_list_id(self, field, list_name, raw):
        list_id = (raw or "").strip()
        first_name = self.office_lists[list_name].get(list_id)
        if not list_id or list_id == "0":
            return None
        if not first_name:
            self.stats[field]["unresolved"] += 1
            self.unresolved[field][f"{list_id} (not in {list_name} list)"] += 1
            return None
        return self._resolve(field, (list_name, list_id), f"{list_name} #{list_id} {first_name}",
                             lambda: self._person_from_first_name(first_name),
                             first_name_only=True)

    # -- reporting ---------------------------------------------------------
    def report_lines(self):
        lines = []
        for field in sorted(self.stats):
            s = self.stats[field]
            total = sum(s.values())
            lines.append(f"{field:38s} rows={total:6d} hcp_id={s['hcp_id']:6d} "
                         f"name={s['name'] + s['first_name']:6d} unresolved={s['unresolved']:6d} "
                         f"({100 * (total - s['unresolved']) / total:5.1f}% linked)")
        if self.conflicts:
            lines.append("\nClock numbers whose HCP user is a different person (not linked by ID):")
            for clock, (name, uids) in sorted(self.conflicts.items()):
                lines.append(f"  {clock:>5s}  Caspio: {name:30s} Odyssey user id(s): {uids}")
        return lines

    def report_rows(self):
        for field, counter in sorted(self.unresolved.items()):
            for ref, n in counter.most_common():
                yield field, ref, n
