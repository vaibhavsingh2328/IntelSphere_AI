#!/usr/bin/env python3
"""IntelSphere local persistence server: Python 3.10+, no third-party packages."""
from __future__ import annotations
from contextlib import closing
import argparse
import http.cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
WEB=ROOT/"web"
MAX_BYTES=8_000_000
CLASSES=("Positive","Neutral","Negative")
THEMES=("offline","performance","integrations","collaboration","pricing","search","onboarding","support")

def validate_state(w):
    def require(ok,message):
        if not ok:raise ValueError(message)
    def text(value,limit,nonempty=False):
        return isinstance(value,str) and len(value)<=limit and (not nonempty or bool(value.strip()))
    def review(r):
        require(isinstance(r,dict),"Invalid review.")
        require(text(r.get("id"),200,True) and text(r.get("text"),5000,True),"Invalid review identifier or text.")
        require(text(r.get("competitor"),100,True) and text(r.get("platform"),100,True),"Missing competitor or platform.")
        require(r.get("origin") in ("Synthetic","Imported"),"Unknown data origin.")
        require(r.get("sentimentOverride") is None or r.get("sentimentOverride") in CLASSES,"Invalid human sentiment label.")
        require(text(r.get("reviewNote",""),2000),"Invalid review note.")
        rating=r.get("rating")
        require(rating is None or (type(rating) is int and 1<=rating<=5),"Invalid rating.")
        date=r.get("date")
        if date:
            from datetime import date as date_type
            require(text(date,10) and date_type.fromisoformat(date).isoformat()==date,"Invalid review date.")
        url=r.get("sourceURL","")
        require(text(url,2000),"Invalid source URL.")
        if url:require(urlsplit(url).scheme in ("http","https") and bool(urlsplit(url).netloc),"Invalid source URL.")
    require(isinstance(w,dict) and w.get("schemaVersion")==1,"Unsupported workspace.")
    require(text(w.get("projectName"),100,True),"Add a project name.")
    require(isinstance(w.get("reviews"),list) and len(w["reviews"])<=1500,"Maximum 1,500 reviews.")
    ids=set()
    for r in w["reviews"]:
        review(r);require(r["id"] not in ids,"Duplicate review IDs.");ids.add(r["id"])
    require(isinstance(w.get("rice"),dict),"Invalid RICE settings.")
    def rice(v,reach_required=False):
        require(isinstance(v,dict),"Invalid RICE input.")
        for field in ("impact","confidence","effort"):
            require(type(v.get(field)) in (int,float),"RICE fields must be numbers.")
        import math
        require(all(math.isfinite(v[field]) for field in ("impact","confidence","effort")),"RICE fields must be finite.")
        require(0<=v["impact"]<=3 and 0<=v["confidence"]<=1 and v["effort"]>0,"Invalid RICE range.")
        if reach_required:require(type(v.get("reach")) in (int,float) and v["reach"]>=0,"Invalid reach proxy.")
    for theme,values in w["rice"].items():
        require(theme in THEMES,"Unknown RICE theme.");rice(values)
    require(isinstance(w.get("roadmap"),list) and len(w["roadmap"])<=30,"Invalid roadmap.")
    roadmap_ids=set()
    for s in w["roadmap"]:
        require(isinstance(s,dict) and text(s.get("id"),200,True) and s["id"] not in roadmap_ids,"Invalid roadmap ID.");roadmap_ids.add(s["id"])
        require(s.get("themeId") in THEMES and text(s.get("title"),500,True),"Invalid roadmap theme or title.")
        require(text(s.get("text"),200000,True) and text(s.get("owner",""),100),"Invalid PRD text or owner.")
        require(s.get("stage") in ("Discovery","Validated","Planned","Deferred"),"Invalid discovery stage.")
        require(isinstance(s.get("filters"),dict) and text(s.get("hash"),200),"Invalid snapshot.")
        rice(s.get("inputs"),True)
        require(isinstance(s.get("evidence"),list) and len(s["evidence"])<=20,"Invalid snapshot evidence.")
        for r in s["evidence"]:review(r)
    require(isinstance(w.get("activity"),list) and len(w["activity"])<=150,"Invalid activity log.")
    for a in w["activity"]:
        require(isinstance(a,dict) and text(a.get("id"),200) and text(a.get("text"),2000) and text(a.get("at"),100),"Invalid activity event.")
    return w

def initialize_db(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path)) as db,db:
        db.execute("CREATE TABLE IF NOT EXISTS workspace(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, revision INTEGER NOT NULL)")
    return path

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,db_path):
        super().__init__(address,Handler)
        self.db_path=initialize_db(db_path)
        self.token=secrets.token_urlsafe(32)

class Handler(BaseHTTPRequestHandler):
    server_version="IntelSphere/1.0"
    def log_message(self,*args):pass
    def json_response(self,data,status=200):
        body=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def allowed_host(self):
        return self.headers.get("Host") in ("127.0.0.1:"+str(self.server.server_port),"localhost:"+str(self.server.server_port))
    def guard(self):
        port=str(self.server.server_port);origin=self.headers.get("Origin")
        if not self.allowed_host() or (origin and origin not in ("http://127.0.0.1:"+port,"http://localhost:"+port)):
            self.json_response({"error":"Invalid origin or host."},403);return False
        c=http.cookies.SimpleCookie()
        try:
            c.load(self.headers.get("Cookie",""))
            if not secrets.compare_digest(c["intelsphere_session"].value,self.server.token):raise KeyError()
        except (KeyError,http.cookies.CookieError):
            self.json_response({"error":"Open the app home page before using its API."},401);return False
        return True
    def do_GET(self):
        if not self.allowed_host():
            self.json_response({"error":"Invalid host."},403);return
        path=urlsplit(self.path).path
        if path=="/api/workspace":
            if not self.guard():return
            with closing(sqlite3.connect(self.server.db_path)) as db,db:
                row=db.execute("SELECT payload,revision FROM workspace WHERE id=1").fetchone()
            self.json_response({"workspace":json.loads(row[0]) if row else None,"revision":row[1] if row else 0});return
        allowed={"/":"index.html","/index.html":"index.html","/app.js":"app.js","/engine.js":"engine.js","/style.css":"style.css","/favicon.svg":"favicon.svg"}
        name=allowed.get(path)
        if not name:
            self.json_response({"error":"Not found."},404);return
        body=(WEB/name).read_bytes()
        mime={".html":"text/html",".js":"text/javascript",".css":"text/css",".svg":"image/svg+xml"}[Path(name).suffix]
        self.send_response(200);self.send_header("Content-Type",mime+"; charset=utf-8")
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if name=="index.html":self.send_header("Set-Cookie","intelsphere_session="+self.server.token+"; HttpOnly; SameSite=Strict; Path=/")
        self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_PUT(self):
        if not self.guard():return
        if self.path!="/api/workspace":
            self.json_response({"error":"Not found."},404);return
        try:
            n=int(self.headers.get("Content-Length","0"))
            if not 0<n<=MAX_BYTES:raise ValueError("Request exceeds 8 MB.")
            body=json.loads(self.rfile.read(n));rev=body.get("revision")
            if type(rev) is not int or rev<0:raise ValueError("Invalid revision.")
            w=validate_state(body.get("workspace"))
            payload=json.dumps(w,ensure_ascii=False,allow_nan=False)
            with closing(sqlite3.connect(self.server.db_path)) as db,db:
                if rev==0:result=db.execute("INSERT OR IGNORE INTO workspace(id,payload,revision) VALUES(1,?,1)",(payload,))
                else:result=db.execute("UPDATE workspace SET payload=?,revision=revision+1 WHERE id=1 AND revision=?",(payload,rev))
                if result.rowcount!=1:
                    self.json_response({"error":"A newer server save exists. Export changes, then reload before saving."},409);return
            self.json_response({"revision":rev+1})
        except (ValueError,TypeError,KeyError) as e:self.json_response({"error":str(e)[:250]},400)
        except Exception:self.json_response({"error":"Saving failed. Export a backup and check local disk access."},500)

def main():
    parser=argparse.ArgumentParser(description="Run IntelSphere locally without installing packages.")
    parser.add_argument("--port",type=int,default=8766)
    parser.add_argument("--data-dir",default=str(ROOT/"runtime-data"))
    args=parser.parse_args();server=Server(("127.0.0.1",args.port),Path(args.data_dir)/"intelsphere.sqlite3")
    print("IntelSphere is ready: http://127.0.0.1:%d"%server.server_port,flush=True)
    print("Analysis runs locally in your browser. No provider key is required.",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=="__main__":main()


