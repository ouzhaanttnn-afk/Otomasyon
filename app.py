"""Local dashboard for Beyin 101.

Generation takes minutes and needs ffmpeg plus a writable disk, so it runs in a
background thread here and the page polls for progress. This deliberately does
not target a serverless host: video assembly cannot run inside a short-lived,
read-only function.
"""
from __future__ import annotations

import threading
import traceback
import uuid
from dataclasses import dataclass, field

from flask import Flask, jsonify, render_template_string, request

from beyin101.config import Config, ConfigError
from beyin101.pipeline import generate
from beyin101.topics import BY_SLUG, TOPICS

app = Flask(__name__)


@dataclass
class Job:
    id: str
    slug: str
    state: str = "queued"          # queued | running | done | error
    message: str = "Sıraya alındı"
    outputs: list[str] = field(default_factory=list)


JOBS: dict[str, Job] = {}
LOCK = threading.Lock()


def _worker(job: Job) -> None:
    topic = BY_SLUG[job.slug]
    try:
        with LOCK:                  # ffmpeg and the API quota are shared
            job.state = "running"
            job.message = "Üretim başladı, bu birkaç dakika sürer…"
            result = generate(topic, Config.load())
        job.state = "done"
        job.message = f"Tamamlandı ({result.seconds / 60:.1f} dakika)"
        job.outputs = [result.long_video.name] + [s.name for s in result.shorts]
    except Exception as exc:        # surface the reason, keep the server up
        job.state = "error"
        job.message = str(exc)
        traceback.print_exc()


PAGE = """<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Beyin 101 — Video Üretici</title>
<style>
 :root{color-scheme:light dark}
 body{font:16px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;
      background:#f4f5f7;color:#16181d}
 @media(prefers-color-scheme:dark){body{background:#14161a;color:#e8eaed}}
 .wrap{max-width:720px;margin:0 auto;padding:40px 20px}
 h1{font-size:24px;margin:0 0 4px}
 p.sub{margin:0 0 28px;opacity:.7;font-size:14px}
 .card{background:#fff;border-radius:10px;padding:16px 18px;margin-bottom:12px;
       display:flex;align-items:center;gap:14px;
       box-shadow:0 1px 3px rgba(0,0,0,.08)}
 @media(prefers-color-scheme:dark){.card{background:#1d2026;box-shadow:none;
       border:1px solid #2a2e36}}
 .card b{flex:1;font-weight:600}
 button{background:#2f6df6;color:#fff;border:0;border-radius:7px;
        padding:9px 16px;font-size:14px;font-weight:600;cursor:pointer}
 button:disabled{opacity:.5;cursor:default}
 .status{font-size:13px;opacity:.75;margin-top:6px}
 .err{color:#d33}
 .ok{color:#1a8a4a}
</style></head><body><div class="wrap">
<h1>🧠 Beyin 101</h1>
<p class="sub">Konu seç, video ve Shorts otomatik üretilsin. Üretim birkaç dakika sürer.</p>
{% for t in topics %}
<div class="card">
  <b>{{ t.title }}</b>
  <button id="b-{{ t.slug }}" onclick="go('{{ t.slug }}')">Üret</button>
</div>
<div class="status" id="s-{{ t.slug }}"></div>
{% endfor %}
<script>
async function go(slug){
  const btn=document.getElementById('b-'+slug), out=document.getElementById('s-'+slug);
  btn.disabled=true; out.className='status'; out.textContent='Başlatılıyor…';
  const r=await fetch('/api/generate',{method:'POST',
      headers:{'Content-Type':'application/json'},body:JSON.stringify({topic:slug})});
  const j=await r.json();
  if(!r.ok){out.className='status err';out.textContent=j.error;btn.disabled=false;return;}
  poll(j.job, slug);
}
async function poll(id, slug){
  const btn=document.getElementById('b-'+slug), out=document.getElementById('s-'+slug);
  const r=await fetch('/api/status/'+id); const j=await r.json();
  out.textContent=j.message;
  if(j.state==='done'){
    out.className='status ok';
    out.textContent=j.message+' → '+j.outputs.join(', ');
    btn.disabled=false; return;
  }
  if(j.state==='error'){out.className='status err';btn.disabled=false;return;}
  setTimeout(()=>poll(id,slug), 3000);
}
</script></div></body></html>"""


@app.route("/")
def index():
    return render_template_string(PAGE, topics=TOPICS)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    slug = (request.get_json(silent=True) or {}).get("topic")
    if slug not in BY_SLUG:
        return jsonify(error="Geçersiz konu"), 400
    try:
        Config.load()
    except ConfigError as exc:
        return jsonify(error=str(exc)), 400

    job = Job(id=uuid.uuid4().hex[:12], slug=slug)
    JOBS[job.id] = job
    threading.Thread(target=_worker, args=(job,), daemon=True).start()
    return jsonify(job=job.id)


@app.route("/api/status/<job_id>")
def api_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(error="Bilinmeyen iş"), 404
    return jsonify(state=job.state, message=job.message, outputs=job.outputs)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
