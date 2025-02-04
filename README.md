# MiniWebServer
HTTP web server for micropython for serving files to a browser and creating REST APIs.
The web server is built with asyncio for handling many requests efficiently.

# Install
Download and copy code files to your project folder.

# Features

## Initialize a web server

Create a web server on host `0.0.0.0` and port `80`:
```python
from miniwebserver import WebServer, MIMEType, Request

app = WebServer(host="0.0.0.0", port=80, source_folder="src")
```

The `source_folder` option allows to define where files to be served are stored.

## Serve static files

When the web server receives a GET request for some file, it will look for it in:
* `source_folder`
* `source_folder`/assets/
* `source_folder`/assets/extension/                    # extension can be css, js, html, ...

Example file architecture:
```
src/
    index.html
    assets/
        js/
            ... js scripts
        css/
            ... css styles
```

## Add custom routes

Custom routes can be defined using the `Webser.get()`, `Webser.post()`, `Webser.put()`, `Webser.delete()` and 
`Webser.patch()` decorators, over route callbacks.
Route callbacks may return a string, bytes or a Response object.

```python
from miniwebserver import File

@app.get("/")
def index() -> bytes:
    return File("src/index.html")                  # return the path to a file to serve for the route "/"


from miniwebserver import MIMEType, Request

@app.post("/api/data", mime_type=MIMEType.json)    # you can specify the MIME type of the returned data, if not HTML
def api_post_data(request: Request) -> str:        # routes other than GET receive the Request object
    return json.dumps({"data": 123})


@app.get("/api/data/{item}", MIMEType.json)        # routes can contain "parameters" to have a single callback respond
def api_get_data_item(item: str) -> str:           # to a range of routes. The parameters values, as received in the 
                                                   # request are passed as callback parameters.
    return json.dumps({"data": SOME_DATA[item]})


from miniwebserver import Response, Version, Code, Header

@app.get("/api/test")                              # you can fully control the response that will be sent to the client
def api_get_test() -> Response:                    # by building the Response object yourself
    body = b"Hello world!"

    return Response(Version(1, 1), Code.s200, headers={
        Header.ContentType: MIMEType.json,
        Header.ContentLength: len(body)
        Header.Connection: Header.ConnectionV.KeepAlive,
    }, body=body)


from miniwebserver import html_document

@app.get("/api/index")                             # to build HTML pages dynamically, you can use the convenience
def api_get_index() -> bytes:                      # function `html_document` to provide the necessary boilerplate
    return html_document(
        title="API",
        head="""<style>
    body {
      padding: 1rem 4rem;
    }
    </style>""",
        body="<h1>API home</h1>")
```

## Templating

MiniWebServer comes with a minimalistic templating engine using [Jinja](https://jinja.palletsprojects.com/en/stable/)'s 
syntax.
For the moment, only `{{ ... }}` expressions and `{% for ... %} ... {% endfor %}` statements are supported.

```python
from miniwebserver.template import parse

parse("path/to/file.any", a=1, b=2, c=3)    # get parsed file's content, passing variable values needed by the template
```
