import os,sqlite3,json,base64,hmac,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).parent
DATA=Path(os.getenv("DATA_DIR","/app/data"));DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/"exaplay.sqlite3"
lock=threading.RLock()
COLS=["name","company","country","email","role","priority","decision","owner","invitation","done","feedback","rsvp","hotel","food","plus_one","notes"]
SEEDS=[
("Dimitris","Omikron","GR"),("Christian Kuntze","Sigma","DE","ck@sigma-av.com"),("Andre Bauer","M2 Projects","DE"),("Maarten van Sloten","Specialelektronik","NL"),("Andreas Schulze","inSynergie","DE","schulze@insynergie.de"),("Manuel Meck","BeWunder","DE"),("Sven Fischer","Project Syntropy","DE"),("Fabian Miodek","Aufwind","DE"),("Sebastian Geenz","Kontakt pruefen","DE"),("Guillem","Mago Pop","ES"),("Lutz Bayer","Aufwind Group","DE"),("Eddy Yanto","Omnigram","SG"),("Bernhard Wohlmacher","Lleyendecker","DE"),("John Mould","ST Engineering Antycip","UK"),("Morgan Wong","Dataton-Umfeld","UK"),("Jose Lopez de Paula","Mago Pop","ES"),("Eirik Jahre","NexusExperia","NO"),("Dustin Mueller","studio : 3","DE"),("Fedor Stuhrmann","studio : 3","DE"),("Bodo Gottschalk","STUDIO6","DE"),("Martin Vronsky","Signal Space","CZ"),("Misha","L&F","UK"),("Tobias Mayer","satis&fy","DE","TobiasMayer@satis-fy.com"),("Daniel Seeger","Neumann & Mueller","DE","Daniel.Seeger@neumannmueller.com"),("Simon Reed","Beyond Light","UK"),("Alexandre Willame","Trio-Tech","BE"),("Vangelis Petridis","Omikron","GR","petridis@omikron.gr"),("Peter Topping","DVS","UK"),("Noemie Waterlot","VIDEMUS","FR"),("David Butler","Pixsper","UK"),("Hardeep Toor","Pixel Frame","UK"),("Barret Hodgson","Vent Media","UK"),("Tomás Saragaço","Independent media engineer","PT"),("Dennis Pohland","DP Entertainment","DE"),("Manuel Breithaupt","Pixway","DE"),("Paul Meffert","Pixway","DE"),("Sebastian Sittig","media ivent","DE"),("Stefan Ihmig","RE:SORB","DE"),("Brad Hurle","Diverse AV","AU"),("Michael Mueller","HAMACO-Umfeld","DE"),("Rossi TC Chou","BenQ","TW"),("Ben Moors","BenQ","EU"),("Matteo","Epson","EU"),("Daniel / technical lead","N&M / technical","DE"),("Technischer Lead","Virtuality.one","DE"),("Technischer Lead","pixel.formation","DE"),("Technischer Lead","Ktech Media Solutions","UK"),("Technischer Lead","Videlio","FR"),("Technischer Lead","ADSI","FR"),("Technischer Lead","VIDEMUS","FR")]
def conn():
 c=sqlite3.connect(DB,timeout=20);c.row_factory=sqlite3.Row;c.execute("PRAGMA busy_timeout=20000");return c
def init():
 with lock,conn() as c:
  c.execute("PRAGMA journal_mode=WAL")
  c.execute("""CREATE TABLE IF NOT EXISTS guests(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,company TEXT NOT NULL,country TEXT DEFAULT '',email TEXT DEFAULT '',role TEXT DEFAULT '',priority TEXT DEFAULT 'B',decision TEXT DEFAULT 'Offen',owner TEXT DEFAULT '',invitation TEXT DEFAULT '',done INTEGER DEFAULT 0,feedback TEXT DEFAULT '',rsvp TEXT DEFAULT 'Offen',hotel TEXT DEFAULT '',food TEXT DEFAULT '',plus_one TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
  if c.execute("SELECT COUNT(*) FROM guests").fetchone()[0]==0:
   for s in SEEDS:
    c.execute("INSERT INTO guests(name,company,country,email,notes) VALUES(?,?,?,?,?)",(s[0],s[1],s[2],s[3] if len(s)>3 else "","Bring an additional technical colleague if useful" if s[0] in ("Andreas Schulze","Tobias Mayer","Christian Kuntze","Daniel Seeger") else ""))
class API(BaseHTTPRequestHandler):
 def out(self,status,obj,ctype="application/json; charset=utf-8"):
  b=(json.dumps(obj,ensure_ascii=False).encode() if ctype.startswith("application/json") else obj)
  self.send_response(status);self.send_header("Content-Type",ctype);self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def auth(self):
  user=os.getenv("APP_USER");pw=os.getenv("APP_PASSWORD")
  if not user or not pw:self.out(503,{"error":"Configure APP_USER and APP_PASSWORD"});return False
  try:
   typ,token=self.headers.get("Authorization","").split(" ",1)
   provided=base64.b64decode(token,validate=True).decode()
   okay=typ.lower()=="basic" and hmac.compare_digest(provided,user+":"+pw)
  except (ValueError,UnicodeError):okay=False
  if not okay:
   self.send_response(401);self.send_header("WWW-Authenticate",'Basic realm="EXAPLAY Guest Lab"');self.send_header("Content-Length","0");self.end_headers()
  return okay
 def body(self):
  length=int(self.headers.get("Content-Length","0"))
  if length<=0 or length>100000:raise ValueError("Invalid size")
  obj=json.loads(self.rfile.read(length))
  if not isinstance(obj,dict) or any(k not in COLS for k in obj):raise ValueError("Invalid fields")
  for k,v in obj.items():
   if k=="done":
    if not isinstance(v,(bool,int)):raise ValueError("Invalid done")
   elif not isinstance(v,str) or len(v)>12000:raise ValueError("Invalid text")
  if "decision" in obj and obj["decision"] not in ("Ja","Nein","Offen"):raise ValueError("Invalid decision")
  if "rsvp" in obj and obj["rsvp"] not in ("Offen","Zusage","Absage","Vielleicht"):raise ValueError("Invalid RSVP")
  return obj
 def do_GET(self):
  path=urlparse(self.path).path
  if path=="/api/health":return self.out(200,{"ok":True})
  if not self.auth():return
  if path=="/api/guests":
   with lock,conn() as c: rows=[dict(x) for x in c.execute("SELECT * FROM guests ORDER BY id")]
   return self.out(200,rows)
  if path=="/event":return self.out(200,(ROOT/"event.html").read_bytes(),"text/html; charset=utf-8")
  if path in ("/","/index.html"):return self.out(200,(ROOT/"index.html").read_bytes(),"text/html; charset=utf-8")
  return self.out(404,{"error":"Not found"})
 def do_POST(self):
  if not self.auth():return
  if urlparse(self.path).path!="/api/guests":return self.out(404,{"error":"Not found"})
  try:
   o=self.body()
   if not o.get("name","").strip() or not o.get("company","").strip():raise ValueError("Name and company required")
   keys=list(o)
   with lock,conn() as c: cur=c.execute("INSERT INTO guests("+",".join(keys)+") VALUES("+",".join("?" for _ in keys)+")",tuple(o.values()))
   return self.out(201,{"id":cur.lastrowid})
  except (ValueError,json.JSONDecodeError) as e:return self.out(400,{"error":str(e)})
 def do_PATCH(self):
  if not self.auth():return
  try:
   n=int(urlparse(self.path).path.split("/")[-1]);o=self.body()
   if not o:raise ValueError("No changes")
   keys=list(o)
   with lock,conn() as c:
    result=c.execute("UPDATE guests SET "+",".join(k+"=?" for k in keys)+",updated_at=CURRENT_TIMESTAMP WHERE id=?",tuple(o.values())+(n,))
   return self.out(200 if result.rowcount else 404,{"ok":bool(result.rowcount)})
  except (ValueError,json.JSONDecodeError) as e:return self.out(400,{"error":str(e)})
 def do_DELETE(self):
  if not self.auth():return
  try:n=int(urlparse(self.path).path.split("/")[-1])
  except ValueError:return self.out(404,{"error":"Invalid id"})
  with lock,conn() as c:c.execute("DELETE FROM guests WHERE id=?",(n,))
  return self.out(200,{"ok":True})
if __name__=="__main__":
 init()
 ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","8080"))),API).serve_forever()
