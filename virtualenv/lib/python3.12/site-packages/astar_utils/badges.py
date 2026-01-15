# -*- coding: utf-8 -*-
"""Everything to do with report badges and more.

Currently only used in IRDB, but has possible applications elsewhere.
"""

from pathlib import Path
from typing import TextIO, Any
from numbers import Number
from string import Template
from collections.abc import Mapping

import yaml

from .nested_mapping import NestedMapping
from .loggers import get_logger

logger = get_logger(__name__)


def _fix_badge_str(badge_str: str) -> str:
    """Eliminate any spaces and single dashes in badge string."""
    return badge_str.replace(" ", "_").replace("-", "--")


class Badge:
    """Base class for markdown report badges.

    Originally created for package status reports in the
    `IRDB <https://github.com/AstarVienna/irdb>`_, but future applications
    outside this is explicitly intended.

    Based on the type and (in case of strings) value of the parameter `value`,
    the appropriate subclass is returned, which also deals with the colour of
    the badge. These subclasses should *not* be instantiated directly, but
    rather this base class should always be used.

    In the case of a string-type `value`, the colour of the badge is based on
    a set of special strings, e.g. red for 'error' or green for 'found'.
    A complete list of these special strings can be accessed via
    ``StrBadge.special_strings``. The default colour for any string value not
    listed as a special string is lightgrey.

    By default, all badges appear as "key/label-value" badges with a grey label
    on the left side and a coloured value on the right side. For simple
    messages, it is also possible to produce a "message-only" badge. This can
    simply be done by adding a leading '!' to the (string) `value` parameter.
    The message of the badge is then only the `key` parameter, while the colour
    of the badge is again decided by the special strings, after the leading '!'
    is stripped.

    Any spaces or single dashes present in either `key` or `value` are
    automatically replaced by underscores or double dashes, respectively, to
    comply with the format requirements for the badges.

    It is possible to manually change the colour of any badge after creation
    by setting the desired colour (string) for the `colour` attribute.

    Parameters
    ----------
    key : str
        Dictionary key, become (left-side) label of the badge.
    value : str, bool, int or float
        Dictionary key, become (right-side) value of the badge.
        Subclass dispatch is decided based on type and value of this parameter.

    Attributes
    ----------
    colour : str
        The (auto-assigned) colour of the badge.
    """

    pattern = Template("[![](https://img.shields.io/badge/$key-$val-$col)]()")
    colour = "lightgrey"

    def __new__(cls, key: str, value):
        """Override creation to create subclasses."""
        if isinstance(value, bool):
            return super().__new__(BoolBadge)
        if isinstance(value, Number):
            return super().__new__(NumBadge)
        if isinstance(value, str):
            if value.startswith("!"):
                return super().__new__(MsgOnlyBadge)
            return super().__new__(StrBadge)
        raise TypeError(value)

    def __init__(self, key: str, value):
        self.key = _fix_badge_str(key)
        self.value = _fix_badge_str(value) if isinstance(value, str) else value

    def write(self, stream: TextIO) -> None:
        """Write formatted pattern to I/O stream."""
        _dict = {"key": self.key, "val": self.value, "col": self.colour}
        stream.write(self.pattern.substitute(_dict))


class BoolBadge(Badge):
    """Key-value Badge for bool values, True -> green, False -> red."""

    colour = "red"

    def __init__(self, key: str, value: bool):
        super().__init__(key, value)
        if self.value:
            self.colour = "green"


class NumBadge(Badge):
    """Key-value Badge for numerical values, lightblue."""

    colour = "lightblue"


class StrBadge(Badge):
    """Key-value Badge for string values, colour based on special strings."""

    # TODO: Special strings such as "observation", "support" and to some ectent
    #       also "missing", "incomplete", "found" and "not_found" are specific
    #       to the IRDB. Perhaps introduce a way to exent the special strings
    #       dict in a ceratin context and then remove the specific values from
    #       here and only keep general ones such as "error", "warning", "ok"...

    special_strings = {
        "observation": "blueviolet",
        "support": "deepskyblue",
        "error": "red",
        "missing": "red",
        "warning": "orange",
        "conflict": "orange",
        "incomplete": "orange",
        "ok": "green",
        "found": "green",
        "not_found": "red",
        "none": "yellowgreen",
    }

    def __init__(self, key: str, value: str):
        super().__init__(key, value)
        self.colour = self.special_strings.get(self.value.lower(), "lightgrey")


class MsgOnlyBadge(StrBadge):
    """Key-only Badge for string values, colour based on special strings."""

    pattern = Template("[![](https://img.shields.io/badge/$key-$col)]()")

    def __init__(self, key: str, value: str):
        super().__init__(key, value.removeprefix("!"))


class BadgeReport(NestedMapping):
    """Context manager class for collection and generation of report badges.

    Intended usage is in a pytest fixture with a scope that covers all tests
    that should be included in that report file:

    >>> import pytest
    >>>
    >>> @pytest.fixture(name="badges", scope="module")
    >>> def fixture_badges():
    >>>     with BadgeReport() as report:
    >>>         yield report

    This fixture can then be used inside the tests like a dictionary:

    >>> def test_something(self, badges):
    >>>     badges[f"!foo.bar.baz"] = "OK"

    Because `BadgeReport` inherits from ``SystemDict``, the use of '!'-type
    "bang-strings" is supported.

    Additionally, any logging generated within a test can be captured and
    stored in the report, to be written in a separate log file at teardown:

    >>> import logging
    >>>
    >>> def test_something_else(self, badges, caplog):
    >>>     logging.warning("Oh no!")
    >>>     badges.logs.extend(caplog.records)

    Note the use of ``caplog.records`` to access the ``logging.LogRecord``
    objects rather then the string output, as `BadgeReport` performs very basic
    custom formatting. Further note the use of ``logs.extend()``, because
    ``caplog.records`` returns a ``list``, to not end up with nested lists.

    The level of logging recorded is controlled by the logging settings in the
    test script. `BadgeReport` handles all ``logging.LogRecord`` objects in
    the final `.logs` list.

    Parameters
    ----------
    filename : str, optional
        Name for yaml file, should end in '.yaml. The default is "badges.yaml".
    report_filename : str, optional
        Name for report file, should end in '.md'. The default is "badges.md".
    logs_filename : str, optional
        Name for log file. The default is "badge_report_log.txt".
    save_logs : bool, optional
        Whether to output logs. The default is True.
    base_path: Path, optional
        Directory to use for reports. Defaults to ./_REPORTS.

    Attributes
    ----------
    yamlpath : Path
        Full path for yaml file.
    report_path : Path
        Full path for report file.
    log_path : Path
        Full path for log file.
    logs : list of logging.LogRecord
        List of logging.LogRecord objects to be saved to `logs_filename`.
    """

    def __init__(
        self,
        filename: str = "badges.yaml",
        report_filename: str = "badges.md",
        logs_filename: str = "badge_report_log.txt",
        save_logs: bool = True,
        base_path=None,
    ):
        logger.debug("REPORT INIT")
        if base_path is not None:
            base_path = Path(base_path)
        else:
            base_path = Path("./_REPORTS")
            logger.debug("base_path not set, using %s", base_path.absolute())

        self.filename = filename
        self.yamlpath = base_path / self.filename
        self.report_name = report_filename
        self.report_path = base_path / self.report_name

        self.save_logs = save_logs
        self.logs: list[Any] = []
        logs_name = logs_filename or "badge_report_log.txt"
        self.log_path = base_path / logs_name

        super().__init__()

    def __enter__(self):
        """Context manager __enter__."""
        logger.debug("REPORT ENTER")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Context manager __exit__."""
        logger.debug("REPORT EXIT")
        self.write_yaml()
        self.generate_report()
        if self.save_logs:
            self.write_logs()
        logger.debug("REPORT DONE")

    def write_logs(self) -> None:
        """Dump logs to file (`logs_filename`)."""
        with self.log_path.open("w", encoding="utf-8") as file:
            for log in self.logs:
                file.write(f"{log.levelname}::{log.message}\n")

    def write_yaml(self) -> None:
        """Dump dict to yaml file (`filename`)."""
        dumpstr = yaml.dump(self.dic, sort_keys=False)
        self.yamlpath.write_text(dumpstr, encoding="utf-8")

    def _make_preamble(self) -> str:
        preamble = (
            "# IRDB Packages Report\n\n"
            "For details on errors and conflicts, see badge report log file "
            "in this directory.\n\n"
        )
        return preamble

    def generate_report(self) -> None:
        """Write markdown badge report to `report_filename`."""
        if not self.report_path.suffix == ".md":
            logger.warning(
                "Expected '.md' suffix for report file name, but found %s. "
                "Report file might not be readable.", self.report_path.suffix)
        with self.report_path.open("w", encoding="utf-8") as file:
            file.write(self._make_preamble())
            make_entries(file, self.dic)


def _get_nested_header(key: str, level: int) -> str:
    if level > 2:
        return f"* {key}: "
    return f"{'#' * (level + 2)} {key.title() if level else key}"


def make_entries(stream: TextIO, entry, level=0) -> None:
    """
    Recursively write lines of text from a nested dictionary to text stream.

    Parameters
    ----------
    stream : TextIO
        I/O stream to write the badges to.

    entry : dict, str, bool, float, int
        A level from a nested dictionary

    level : int
        How far down the rabbit hole we are w.r.t the nested dictionary

    Returns
    -------
    None
    """
    if not isinstance(entry, Mapping):
        return

    nest_key = ""
    for key, value in entry.items():
        if nest_key and key.startswith(f"!{nest_key}"):
            # avoid duplication
            continue

        stream.write("\n")
        stream.write("  " * (level - 2))

        if isinstance(value, Mapping):
            stream.write(_get_nested_header(key, level))
            # recursive
            make_entries(stream, value, level=level+1)
        elif key.startswith("!"):
            nest_key = key.removeprefix("!").split(".", maxsplit=1)[0]
            stream.write(_get_nested_header(nest_key, level))
            # recursive
            make_entries(stream, entry[nest_key], level=level+1)
        else:
            if level > 1:
                stream.write("* ")
            Badge(key, value).write(stream)
