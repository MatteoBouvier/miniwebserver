import re

from miniwebserver.config import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any
    from io import TextIOWrapper

PATTERN_EXPRESSION = re.compile("{{(.*?)}}")
PATTERN_STATEMENT = re.compile("{%(.*?)%}")


def _replace(variables: dict[str, "Any"]) -> Callable[[re.Match[str]], str]:
    def inner(match: re.Match[str]) -> str:
        return str(eval(match.group(1).strip(), globals(), variables))

    return inner


def _parse_for(
    statement: str, line_offset: int, file: TextIOWrapper, variables: dict[str, "Any"]
) -> tuple[str, int]:
    if not statement.startswith("for "):
        raise ValueError("Only for statements are allowed")

    var, iterable = statement[4:].split(" in ")

    parsed_for: list[str] = []

    while True:
        line = file.readline()

        if not line:
            raise ValueError("For statement was not closed, expected {% endfor %}")

        else:
            line = line.strip()

        if line.replace(" ", "") == "{%endfor%}":
            break

        else:
            parsed_for.append(line)

    parsed = ""
    line_nb = 1

    for it in variables[iterable]:
        for line_nb, line in enumerate(parsed_for, start=1):
            parsed += _parse_expression(
                line, line_nb + line_offset, variables | {var: it}
            )[0]

    return parsed, line_offset + line_nb


def _parse_expression(
    line: str, line_nb: int, variables: dict[str, "Any"]
) -> tuple[str, int]:
    try:
        return PATTERN_EXPRESSION.sub(_replace(variables), line) + "\n", line_nb + 1

    except NameError as err:
        raise NameError(
            "Template formatting failed at line #{0}\n{1}\n{2}".format(
                line_nb, line, err
            )
        )


def parse(path: str, **variables: "Any") -> str:
    parsed = ""
    line_nb = 1

    with open(path, "r") as file:
        while True:
            line = file.readline()
            if not line:
                break

            else:
                line = line.strip()

            statement_match = PATTERN_STATEMENT.search(line)

            if statement_match is not None:
                statement = line[
                    statement_match.start() + 2 : statement_match.end() - 2
                ].strip()

                parsed_for, line_nb = _parse_for(statement, line_nb, file, variables)
                parsed += parsed_for

            else:
                parsed_expr, line_nb = _parse_expression(line, line_nb, variables)
                parsed += parsed_expr

    return parsed
