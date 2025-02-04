import io
import sys

from miniwebserver.enums import FILE_MARKER


def get_media_types(MIME_type: str) -> list[str]:
    types = [t.split(";q=") if ";" in t else (t, 1) for t in MIME_type.split(",")]
    return [t for (t, _) in sorted(types, key=lambda x: float(x[1]))]


def html_document(title: str, *, head: str = "", body: str = "") -> bytes:
    return b"""<!doctype html>
<html lang="en">
<head>
  <title>%s</title>
  %s
</head>
<body>
  %s
</body>
</html>""" % (title, head, body)


def print_exception(err: Exception) -> bytes:
    """Print exception to stderr AND return traceback formatted to HTML"""
    print("[Warning] An internal error occured:", file=sys.stderr)

    err_str_buffer = io.StringIO()
    sys.print_exception(err, err_str_buffer)
    err_str = err_str_buffer.getvalue()

    return html_document(
        "500 Internal Server Error",
        head="""<style>
body {
  padding: 1rem 4rem;
}

</style>""",
        body="""<h1>Internal Server Error</h1>
<div style="background: #F6C479; border: 1px solid #232326; border-radius: .5rem; padding: 1rem;">
  {0}
</div>""".format(
            err_str.replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        ),
    )


def File(path: str) -> bytes:
    return b"%s%s" % (FILE_MARKER, path)
