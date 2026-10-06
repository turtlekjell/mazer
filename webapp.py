import argparse
import html
import mimetypes
import secrets
import threading
import webbrowser
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from main import DIFFICULTY_COLS, generate_maze_files
from version import __version__


PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "input"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
OUTPUT_DIR = PROJECT_ROOT / "output"
STATIC_DIR = PROJECT_ROOT / "static"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_UPLOAD_BYTES = 16 * 1024 * 1024
MIN_CUSTOM_COLS = 10
MAX_CUSTOM_COLS = 200


class MazerHandler(BaseHTTPRequestHandler):
    server_version = f"MazerLocal/{__version__}"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(render_page())
            return

        if parsed.path == "/static/style.css":
            self._send_file(STATIC_DIR / "style.css", "text/css; charset=utf-8")
            return

        if parsed.path.startswith("/input/"):
            filename = Path(unquote(parsed.path[len("/input/"):])).name
            requested = INPUT_DIR / filename
            if not filename or requested.suffix.lower() not in ALLOWED_EXTENSIONS or not requested.is_file():
                self.send_error(404)
                return
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            self._send_file(requested, content_type)
            return

        if parsed.path.startswith("/output/"):
            filename = Path(unquote(parsed.path[len("/output/"):])).name
            requested = OUTPUT_DIR / filename
            if not filename or not requested.is_file():
                self.send_error(404)
                return
            download = parse_qs(parsed.query).get("download") == ["1"]
            self._send_file(
                requested,
                "image/png",
                attachment_name=filename if download else None,
            )
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/generate":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_html(render_page(error="Invalid request size."), status=400)
            return

        if content_length <= 0 or content_length > MAX_UPLOAD_BYTES:
            self._send_html(
                render_page(error="Use an image smaller than 16 MB."),
                status=413,
            )
            return

        body = self.rfile.read(content_length)
        try:
            fields, upload = parse_multipart_form(self.headers.get("Content-Type", ""), body)
            result, defaults = generate_from_form(fields, upload)
        except ValueError as exc:
            defaults = form_defaults(locals().get("fields", {}))
            self._send_html(render_page(error=str(exc), defaults=defaults), status=400)
            return
        except (OSError, RuntimeError) as exc:
            defaults = form_defaults(locals().get("fields", {}))
            self._send_html(render_page(error=str(exc), defaults=defaults), status=500)
            return

        self._send_html(render_page(result=result, defaults=defaults))

    def log_message(self, fmt, *args):
        print(f"[Mazer] {self.address_string()} - {fmt % args}")

    def _send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path, content_type, attachment_name=None):
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if attachment_name:
            safe_name = attachment_name.replace('"', "")
            self.send_header("Content-Disposition", f'attachment; filename="{safe_name}"')
        self.end_headers()
        self.wfile.write(data)


def list_sample_images():
    """Return tracked/local images available from the input directory."""
    if not INPUT_DIR.exists():
        return []
    return sorted(
        (
            path
            for path in INPUT_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
        ),
        key=lambda path: path.name.lower(),
    )


def sample_display_name(path):
    name = path.stem
    if name.lower().startswith("sample_"):
        name = name[7:]
    return name.replace("_", " ").replace("-", " ").strip().title()


def parse_multipart_form(content_type, body):
    if "multipart/form-data" not in content_type:
        raise ValueError("The browser did not send a valid form submission.")

    raw = (
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        + body
    )
    message = BytesParser(policy=default).parsebytes(raw)
    if not message.is_multipart():
        raise ValueError("The browser did not send a valid form submission.")

    fields = {}
    upload = None
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        payload = part.get_payload(decode=True) or b""
        filename = part.get_filename()
        if filename is not None and name == "image":
            if filename and payload:
                upload = {"filename": filename, "data": payload}
        elif filename is None:
            fields[name] = payload.decode(part.get_content_charset() or "utf-8", errors="replace")

    return fields, upload


def _resolve_source(fields, upload):
    """Choose either the temporary browser upload or a persistent input sample."""
    if upload is not None:
        filename = Path(upload["filename"]).name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError("Use a PNG, JPG/JPEG, or WebP image.")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        upload_path = UPLOAD_DIR / f"{secrets.token_hex(8)}{suffix}"
        upload_path.write_bytes(upload["data"])
        return upload_path, Path(filename).stem, True

    sample_name = Path(fields.get("sample", "")).name
    if not sample_name:
        raise ValueError("Choose a sample image or upload your own image.")

    available = {path.name: path for path in list_sample_images()}
    sample_path = available.get(sample_name)
    if sample_path is None:
        raise ValueError("That sample image is no longer available.")
    return sample_path, sample_path.stem, False


def generate_from_form(fields, upload):
    defaults = form_defaults(fields)
    difficulty = defaults["difficulty"]
    opacity_percent = defaults["opacity"]
    threshold = defaults["threshold"]
    invert = defaults["invert"]

    if difficulty == "custom":
        cols = defaults["custom_cols"]
        if not MIN_CUSTOM_COLS <= cols <= MAX_CUSTOM_COLS:
            raise ValueError(
                f"Custom difficulty must be between {MIN_CUSTOM_COLS} and {MAX_CUSTOM_COLS} cells wide."
            )
        engine_difficulty = "medium"
    elif difficulty in DIFFICULTY_COLS:
        cols = None
        engine_difficulty = difficulty
    else:
        raise ValueError("Choose a valid difficulty level.")

    if not 0 <= opacity_percent <= 50:
        raise ValueError("Background opacity must be between 0% and 50%.")
    if not 0 <= threshold <= 255:
        raise ValueError("Threshold must be between 0 and 255.")

    seed_text = fields.get("seed", "").strip()
    if seed_text:
        try:
            seed = int(seed_text)
        except ValueError as exc:
            raise ValueError("Seed must be a whole number.") from exc
    else:
        seed = secrets.randbelow(2_147_483_647)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source_path, source_stem, temporary = _resolve_source(fields, upload)

    try:
        generated = generate_maze_files(
            image=str(source_path),
            source_stem=source_stem,
            difficulty=engine_difficulty,
            cols=cols,
            threshold=threshold,
            invert=invert,
            seed=seed,
            background_opacity=opacity_percent / 100.0,
            output=OUTPUT_DIR,
        )
    finally:
        if temporary:
            source_path.unlink(missing_ok=True)

    if difficulty == "custom":
        difficulty_label = f"Custom · {cols} cells wide"
    else:
        difficulty_label = generated["difficulty"].capitalize()

    result = {
        "puzzle_id": generated["puzzle_id"],
        "maze_filename": generated["maze_path"].name,
        "solution_filename": generated["solution_path"].name,
        "difficulty": difficulty_label,
        "seed": generated["seed"],
        "grid": f'{generated["maze"].num_cols} × {generated["maze"].num_rows}',
        "path_length": len(generated["maze"].solution_path),
        "source_name": sample_display_name(Path(source_stem)),
    }
    return result, defaults


def form_defaults(fields=None):
    fields = fields or {}
    difficulty = fields.get("difficulty", "medium")
    try:
        opacity = int(fields.get("opacity", "15"))
    except ValueError:
        opacity = 15
    try:
        threshold = int(fields.get("threshold", "160"))
    except ValueError:
        threshold = 160
    try:
        custom_cols = int(fields.get("custom_cols", "150"))
    except ValueError:
        custom_cols = 150
    return {
        "difficulty": difficulty,
        "custom_cols": custom_cols,
        "opacity": opacity,
        "threshold": threshold,
        "invert": fields.get("invert") == "on",
        "sample": Path(fields.get("sample", "")).name,
    }


def render_page(result=None, error=None, defaults=None):
    defaults = defaults or form_defaults()
    difficulty_html = []
    for name, cols in DIFFICULTY_COLS.items():
        checked = " checked" if defaults["difficulty"] == name else ""
        difficulty_html.append(
            f'''<label class="choice"><input type="radio" name="difficulty" value="{name}"{checked}>
            <span><strong>{name.capitalize()}</strong><small>{cols} cells wide</small></span></label>'''
        )

    custom_checked = " checked" if defaults["difficulty"] == "custom" else ""
    difficulty_html.append(
        f'''<label class="choice"><input type="radio" name="difficulty" value="custom"{custom_checked}>
        <span><strong>Custom</strong><small>{MIN_CUSTOM_COLS}–{MAX_CUSTOM_COLS} cells wide</small></span></label>'''
    )

    sample_html = []
    for sample in list_sample_images():
        filename = html.escape(sample.name, quote=True)
        label = html.escape(sample_display_name(sample))
        checked = " checked" if defaults.get("sample") == sample.name else ""
        sample_html.append(
            f'''<label class="sample-card"><input type="radio" name="sample" value="{filename}"{checked}>
            <span><img src="/input/{filename}" alt="{label} sample"><strong>{label}</strong></span></label>'''
        )
    if sample_html:
        samples_section = f'''<div class="source-heading"><strong>Choose a sample</strong><span>Images stored in <code>input/</code></span></div>
        <div class="sample-grid">{''.join(sample_html)}</div><div class="or-divider"><span>or upload your own</span></div>'''
    else:
        samples_section = '''<div class="source-heading"><strong>Choose an image</strong><span>Add reusable samples to <code>input/</code></span></div>'''

    error_html = (
        f'<div class="alert" role="alert">{html.escape(error)}</div>' if error else ""
    )

    result_html = ""
    if result:
        puzzle_id = html.escape(result["puzzle_id"])
        maze_name = html.escape(result["maze_filename"], quote=True)
        solution_name = html.escape(result["solution_filename"], quote=True)
        result_html = f'''
        <section class="results" aria-live="polite">
          <div class="result-heading">
            <div><p class="eyebrow">PUZZLE ID</p><h2>{puzzle_id}</h2></div>
            <div class="meta">{html.escape(result["difficulty"])} · {html.escape(result["grid"])} · seed {result["seed"]}</div>
          </div>
          <div class="preview-grid">
            <article class="preview-card">
              <div class="card-heading"><h3>Maze</h3><span>Print or solve</span></div>
              <a href="/output/{maze_name}" target="_blank" rel="noopener"><img src="/output/{maze_name}" alt="Generated maze"></a>
              <a class="download" href="/output/{maze_name}?download=1">Download maze</a>
            </article>
            <article class="preview-card">
              <div class="card-heading"><h3>Answer key</h3><span>{result["path_length"]}-cell solution</span></div>
              <a href="/output/{solution_name}" target="_blank" rel="noopener"><img src="/output/{solution_name}" alt="Maze answer key with solution path"></a>
              <a class="download" href="/output/{solution_name}?download=1">Download answer key</a>
            </article>
          </div>
        </section>'''

    invert_checked = " checked" if defaults.get("invert") else ""
    custom_disabled = "" if defaults["difficulty"] == "custom" else " disabled"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mazer</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <main class="shell">
    <header class="hero"><p class="eyebrow">LOCAL MAZE MAKER</p><h1>Mazer</h1><p>Turn a picture into a printable maze and matching answer key.</p></header>
    {error_html}
    <section class="panel">
      <form action="/generate" method="post" enctype="multipart/form-data" id="maze-form">
        <fieldset class="source-fieldset"><legend>Image</legend>{samples_section}
          <label class="drop-zone" id="drop-zone" for="image-input" tabindex="0">
            <strong id="file-label">Drop an image here</strong><span>or click to choose PNG, JPG, or WebP</span>
            <input id="image-input" name="image" type="file" accept="image/png,image/jpeg,image/webp">
          </label>
          <p class="form-error" id="source-error" role="alert" hidden>Choose a sample image or upload your own.</p>
        </fieldset>
        <fieldset><legend>Difficulty</legend><div class="difficulty-grid">{''.join(difficulty_html)}</div>
          <div class="custom-difficulty"><label for="custom-cols">Custom width</label>
            <input id="custom-cols" name="custom_cols" type="number" min="{MIN_CUSTOM_COLS}" max="{MAX_CUSTOM_COLS}" value="{defaults['custom_cols']}"{custom_disabled}>
            <span>Up to {MAX_CUSTOM_COLS} cells wide for an intentionally brutal maze.</span></div>
        </fieldset>
        <div class="control-row"><label for="opacity">Background image <strong><span id="opacity-value">{defaults["opacity"]}</span>%</strong></label>
          <input id="opacity" name="opacity" type="range" min="0" max="50" step="1" value="{defaults["opacity"]}"></div>
        <details><summary>Advanced image controls</summary><div class="advanced-grid">
          <label>Threshold<input name="threshold" type="number" min="0" max="255" value="{defaults["threshold"]}"></label>
          <label>Seed <span class="muted">(blank = random)</span><input name="seed" type="number" placeholder="Random"></label>
          <label class="checkbox-row"><input name="invert" type="checkbox"{invert_checked}><span>Invert foreground/background</span></label>
        </div></details>
        <button class="primary" type="submit" id="generate-button">Generate Maze</button>
      </form>
    </section>
    {result_html}
    <footer class="app-footer">Mazer v{__version__} · Runs locally on this computer · <a href="https://github.com/turtlekjell/mazer" target="_blank" rel="noopener">GitHub</a></footer>
  </main>
  <script>
    const input=document.getElementById('image-input'), drop=document.getElementById('drop-zone'), fileLabel=document.getElementById('file-label');
    const opacity=document.getElementById('opacity'), opacityValue=document.getElementById('opacity-value'), button=document.getElementById('generate-button');
    const samples=[...document.querySelectorAll('input[name="sample"]')], difficulties=[...document.querySelectorAll('input[name="difficulty"]')];
    const customCols=document.getElementById('custom-cols'), sourceError=document.getElementById('source-error');
    function chooseUpload(){{samples.forEach(item=>item.checked=false);sourceError.hidden=true;}}
    function chooseSample(){{input.value='';fileLabel.textContent='Drop an image here';sourceError.hidden=true;}}
    function syncCustom(){{const selected=document.querySelector('input[name="difficulty"]:checked');customCols.disabled=!selected||selected.value!=='custom';}}
    input.addEventListener('change',()=>{{if(input.files.length){{fileLabel.textContent=input.files[0].name;chooseUpload();}}}});
    samples.forEach(item=>item.addEventListener('change',chooseSample));
    difficulties.forEach(item=>item.addEventListener('change',syncCustom));
    syncCustom();
    opacity.addEventListener('input',()=>opacityValue.textContent=opacity.value);
    ['dragenter','dragover'].forEach(name=>drop.addEventListener(name,event=>{{event.preventDefault();drop.classList.add('dragging');}}));
    ['dragleave','drop'].forEach(name=>drop.addEventListener(name,event=>{{event.preventDefault();drop.classList.remove('dragging');}}));
    drop.addEventListener('drop',event=>{{if(!event.dataTransfer.files.length)return;input.files=event.dataTransfer.files;fileLabel.textContent=event.dataTransfer.files[0].name;chooseUpload();}});
    document.getElementById('maze-form').addEventListener('submit',event=>{{
      if(!input.files.length&&!document.querySelector('input[name="sample"]:checked')){{event.preventDefault();sourceError.hidden=false;drop.focus();return;}}
      button.disabled=true;button.textContent='Generating…';
    }});
  </script>
</body></html>'''


def run_server(host="127.0.0.1", port=5000, open_browser=True):
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), MazerHandler)
    actual_port = server.server_address[1]
    url = f"http://{host}:{actual_port}"
    print(f"Mazer v{__version__} is running at {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Mazer.")
    finally:
        server.server_close()


def parse_args():
    parser = argparse.ArgumentParser(description="Run the local Mazer browser interface.")
    parser.add_argument("--version", action="version", version=f"Mazer {__version__}")
    parser.add_argument("--port", type=int, default=5000, help="Local port (default: 5000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser automatically")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_server(port=args.port, open_browser=not args.no_browser)
