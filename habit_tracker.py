from __future__ import annotations

import os.path
from datetime import datetime
from enum import Enum
from typing import Optional


# For now, daily habits only.
# TODO: Weekly/monthly/...
# TODO: n times a day/week/month/...
# TODO: Daily but these days: ... (e.g. weekdays), etc.


class Result(Enum):
    GOOD = "+"  # DONE for good habits.
    BAD = "-"   # DONE for bad habits.
    UNKNOWN = "?"

    @staticmethod
    def from_str(s: str) -> Result:
        if s == "+":
            return Result.GOOD
        elif s == "-":
            return Result.BAD
        elif s == "?":
            return Result.UNKNOWN
        else:
            assert False


def _date_to_str(date: datetime) -> str:
    return f"{date.year}-{date.month}-{date.day}"


def _str_to_date(date_str: str) -> datetime:
    return datetime(*map(int, date_str.split("-")))


def _get_today() -> datetime:
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    return today


def _get_today_str() -> str:
    return _date_to_str(_get_today())


class Habit:

    _SEP = "-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-"

    @staticmethod
    def _find_latest_habit_id() -> str:
        os.path.exists("habits")
        habit_ids = os.listdir("habits")
        if len(habit_ids) == 0:
            return "-1"
        return str(max(map(int, habit_ids)))

    @staticmethod
    def _find_habit_id(title: str) -> str:
        desired_habit_id = None

        assert os.path.exists("habits")
        habit_ids = os.listdir("habits")
        for habit_id in habit_ids:
            found_title = Habit._read_habit(habit_id)[0]
            if found_title.lower() == title.lower():
                assert desired_habit_id is None, f"There are more than 1 habits with title '{title}'. (The search is case-insensitive.)"
                desired_habit_id = habit_id

        assert desired_habit_id is not None, f"There is no habit with title '{title}'."
        return desired_habit_id

    @staticmethod
    def _read_habit(habit_id: str) -> tuple[str, str, str, list[Result]]:
        assert os.path.exists("habits")
        assert os.path.exists(f"habits/{habit_id}")

        with open(f"habits/{habit_id}", "r") as f:
            lines = f.read().splitlines()

        assert lines[1] == Habit._SEP

        second_sep_idx = len(lines) - lines[::-1].index(Habit._SEP) - 1
        assert second_sep_idx != 1 and second_sep_idx != 2

        title = lines[0]
        description = "\n".join(lines[2: second_sep_idx])
        start_date_str = lines[second_sep_idx + 1]

        series_lines = lines[second_sep_idx + 2:]
        if series_lines == [""]:
            series = []
        else:
            series = [Result.from_str(line) for line in series_lines]

        return title, description, start_date_str, series

    @staticmethod
    def _write_habit(habit_id: str, title: str, description: str, start_date_str: str, series: list[Result]) -> None:
        if not os.path.exists("habits"):
            os.mkdir("habits")

        with open(f"habits/{habit_id}", "w") as f:
            f.write(title + "\n")
            f.write(Habit._SEP + "\n")
            f.write(description + "\n")
            f.write(Habit._SEP + "\n")
            f.write(start_date_str + "\n")
            f.write(("\n".join([result.value for result in series])) + "\n")

    @staticmethod
    def create(title: str, description: str, start_date_str: Optional[str] = None, series: Optional[list[Result]] = None) -> Habit:
        if not os.path.exists("habits"):
            os.mkdir("habits")

        habit_id = str(int(Habit._find_latest_habit_id()) + 1)

        if start_date_str is None:
            start_date_str = _get_today_str()

        if series is None:
            series = []

        return Habit(habit_id, title, description, start_date_str, series)

    @staticmethod
    def find(habit_id: Optional[str] = None, title: Optional[str] = None) -> Habit:
        if habit_id is None:
            assert title is not None
            habit_id = Habit._find_habit_id(title)
        else:
            assert title is None

        title, description, start_date_str, series = Habit._read_habit(habit_id)
        return Habit(habit_id, title, description, start_date_str, series)

    @staticmethod
    def _get_num_missing_days(start_date_str: str, series: list[Result], including_today: bool = True) -> int:
        start_date = _str_to_date(start_date_str)
        today = _get_today()
        num_days = (today - start_date).days

        assert len(series) <= num_days + 1
        if including_today:
            return num_days - len(series) + 1

        if len(series) == num_days + 1:  # Even today is added.
            return 0
        return num_days - len(series)

    def __init__(self, habit_id: str, title: str, description: str, start_date_str: str, series: list[Result]):
        self._habit_id = habit_id
        self.title = title
        self.description = description
        self._start_date_str = start_date_str
        self._series = series

    def mark_today(self, result: Result) -> None:
        num_missing_days = self.get_num_missing_days(True)
        assert num_missing_days > 0, "Today is already marked!"
        assert num_missing_days == 1, "There are other days missing!"
        self._series.append(result)

    def mark_missing_days(self, results: list[Result], including_today: bool) -> None:
        assert self.get_num_missing_days(including_today) == len(results)
        self._series.extend(results)

    def get_num_missing_days(self, including_today: bool = True) -> int:
        return Habit._get_num_missing_days(self._start_date_str, self._series, including_today)

    def is_today_marked(self) -> bool:
        return self.get_num_missing_days(including_today=True) == 0

    def save(self) -> None:
        Habit._write_habit(self._habit_id, self.title, self.description, self._start_date_str, self._series)

    def remove(self, prompt=True) -> None:
        if prompt:
            choice = input(f"The habit '{self.title}' will be removed. Proceed? (y/N) ").lower()
            if choice == "y":
                os.remove(f"habits/{self._habit_id}")
                print("The habit is removed.")
            else:
                print("The program is terminating.")
                exit(1)
        else:
            os.remove(f"habits/{self._habit_id}")

    def get_habit_id(self):
        return self._habit_id

    def get_start_date_str(self):
        return self._start_date_str

    def get_series(self):
        return self._series  # Return a copy?
