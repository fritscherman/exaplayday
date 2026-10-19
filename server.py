import os,sqlite3,json,base64,hmac,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).parent
STATIC=ROOT/"static"
STATIC_TYPES={".css":"text/css; charset=utf-8",".svg":"image/svg+xml",".png":"image/png",".ico":"image/x-icon",".woff2":"font/woff2"}
DATA=Path(os.getenv("DATA_DIR","/app/data"));DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/"exaplay.sqlite3"
lock=threading.RLock()
COLS=["name","company","country","email","role","priority","decision","owner","invitation","done","feedback","rsvp","hotel","food","plus_one","notes","rating"]
SEEDS=[
("Dimitris","Omikron","GR"),("Christian Kuntze","Sigma","DE","ck@sigma-av.com"),("Andre Bauer","M2 Projects","DE"),("Maarten van Sloten","Specialelektronik","NL"),("Andreas Schulze","inSynergie","DE","schulze@insynergie.de"),("Manuel Meck","BeWunder","DE"),("Sven Fischer","Project Syntropy","DE"),("Fabian Miodek","Aufwind","DE"),("Sebastian Geenz","Kontakt pruefen","DE"),("Guillem","Mago Pop","ES"),("Lutz Bayer","Aufwind Group","DE"),("Eddy Yanto","Omnigram","SG"),("Bernhard Wohlmacher","Lleyendecker","DE"),("John Mould","ST Engineering Antycip","UK"),("Morgan Wong","Dataton-Umfeld","UK"),("Jose Lopez de Paula","Mago Pop","ES"),("Eirik Jahre","NexusExperia","NO"),("Dustin Mueller","studio : 3","DE"),("Fedor Stuhrmann","studio : 3","DE"),("Bodo Gottschalk","STUDIO6","DE"),("Martin Vronsky","Signal Space","CZ"),("Misha","L&F","UK"),("Tobias Mayer","satis&fy","DE","TobiasMayer@satis-fy.com"),("Daniel Seeger","Neumann & Mueller","DE","Daniel.Seeger@neumannmueller.com"),("Simon Reed","Beyond Light","UK"),("Alexandre Willame","Trio-Tech","BE"),("Vangelis Petridis","Omikron","GR","petridis@omikron.gr"),("Peter Topping","DVS","UK"),("Noemie Waterlot","VIDEMUS","FR"),("David Butler","Pixsper","UK"),("Hardeep Toor","Pixel Frame","UK"),("Barret Hodgson","Vent Media","UK"),("Tomás Saragaço","Independent media engineer","PT"),("Dennis Pohland","DP Entertainment","DE"),("Manuel Breithaupt","Pixway","DE"),("Paul Meffert","Pixway","DE"),("Sebastian Sittig","media ivent","DE"),("Stefan Ihmig","RE:SORB","DE"),("Brad Hurle","Diverse AV","AU"),("Rossi TC Chou","BenQ","TW"),("Ben Moors","BenQ","EU"),("Matteo","Epson","EU"),("Daniel / technical lead","N&M / technical","DE"),("Technischer Lead","Virtuality.one","DE"),("Technischer Lead","pixel.formation","DE"),("Technischer Lead","Ktech Media Solutions","UK"),("Technischer Lead","Videlio","FR"),("Technischer Lead","ADSI","FR"),("Technischer Lead","VIDEMUS","FR")]
# Filled from public sources (company sites, imprints, press pages). See README.
PROPOSED_CONTACTS=[
 # Personal addresses, literally published on the company's own site
 ("Lutz Bayer","Aufwind Group","lutz.bayer@aufwind-group.de","personal","aufwind-group.de/de/people","CEO aufwind RIDES (Simulatoren, Media Rides, Dark Rides, Malterdingen). Hook: Podcoaster-Folge PC087 ueber den Weg von der Agentur zum Ride-Hersteller."),
 ("Eddy Yanto","Omnigram","eddy@omnigram.net","personal","omnigram.net (Kontaktadresse), Titel laut AVIXA-Profil","Principal Omnigram Singapore. Listet VIOSO Auto-Alignment auf der eigenen Website. Hook: 'Light of Gelam' Mapping Sultan Mosque, Singapore Odyssea, Wings of Time."),
 ("Hardeep Toor","Pixel Frame","hardeep.toor@pixelframe.co.uk","personal","pixelframe.co.uk","Founder, freelance Video Tech / Technical PM. Media-Server in Millumin und PIXERA, vMix. Konferenzen, Launches, Fashion Shows."),
 ("Florian Miodek","Aufwind","florian.miodek@aufwind-group.de","personal","aufwind-group.de/de/people","Rides-Team aufwind group. Liste nannte 'Fabian', Teamseite fuehrt Florian Miodek."),
 # General company addresses (person not named on the site)
 ("Manuel Meck","BeWunder","contact@bewunder.com","general","bewunder.com/imprint","Hook: USA Pavilion 'America the Beautiful' Expo 2025 Osaka, World Government Summit 2025, Viega Media Experience Center."),
 ("Bernhard Wohlmacher","Lleyendecker","info@lleyendecker.de","general","lleyendecker.de/impressum","LLEYENDECKER GmbH Wuppertal, ~150 MA, Berlin-Niederlassung. Hook: Berlinale 2024, Telekom MWC 2024, Deichbrand 2025."),
 ("Eirik Jahre","NexusExperia","mail@audioteknikk.no","general","audioteknikk.no/kontakt, Dataton-Partnerseite","Firma online nur als Audioteknikk AS (Skedsmokorset, NO) auffindbar, Dataton Premium Partner Norwegen. Hook: Museen/Experience Center (Vikingskipshuset, Lofotr), WATCHOUT seit 2013, Pixilab Blocks."),
 ("Bodo Gottschalk","STUDIO6","kontakt@studio6.berlin","general","studio6.berlin/de/start/impressum","Partner STUDIO6 GbR Berlin (richtige Domain studio6.berlin, nicht studio6.de). Hook: Playmobil Messeabend 2025 (3D-Mapping + Mocap), 'Neue Ufer' Panoramaprojektion Ulm, Rimini Protokoll."),
 ("Martin Vronsky","Signal Space","info@signalspace.com","general","signalspace.com/cs/kontakt","Nicht auf der Website genannt. Signal Space Prag: groesste Digital-Art-Galerie CZ, 300 qm Immersive Room mit 360-Grad-Projektion. Alternativ klara.cerna@signalspace.com (Corporate Events)."),
 ("Peter Topping","DVS","Sales@DVSGroup.com","general","dvsgroup.com/About","DVS = Digital Video Systems Ltd, Weybridge UK (Zuordnung nur ueber Suchtreffer). Hook: 360-Grad Projection-Mapping-Projekt, ISE 2026."),
 ("Barret Hodgson","Vent Media","info@ventmedia.co.uk","general","ventmedia.co.uk, stagelync.com/profile/barret-hodgson","Founder, Video Artist & Projection Designer, Nottingham. Hook: Glastonbury Temple Stage, Tower of London Mapping mit 59 Productions, Notch/Disguise/Pixera, Cirque du Soleil."),
 ("Dennis Pohland","DP Entertainment","info@dpentertain.de","general","dpentertainment.de/impressum","Geschaeftsfuehrer DP Entertainment GmbH, Stahnsdorf. Hook: PIXERA two Gen2 Quad im Dry-Hire, 90 Jahre BEUMER Group, CHAMPIONS 2025, K5."),
 ("Manuel Breithaupt","Pixway","mail@pixway.com","general","pixway.com/imprint","Geschaeftsfuehrer Pixway GmbH Berlin (+ Las Vegas), disguise Partner, XR/Virtual Production. Hook: Helene Fischer Stadiontour, USBEK15 Mapping."),
 ("Paul Meffert","Pixway","mail@pixway.com","general","pixway.com/imprint","Geschaeftsfuehrer Pixway GmbH Berlin. Siehe Manuel Breithaupt, ggf. nur einen der beiden einladen."),
 ("Sebastian Sittig","media ivent","welcome@media-ivent.com","general","media-ivent.de/impressum","Im Impressum als Verantwortlicher genannt, Potsdam-Babelsberg. Hook: Henkel CES 2025 (Showcontrol via iPad/Watch), Audi Auto Shanghai 2025, 'Garden of Light' Fassadenmapping Berlin, LightAct Server."),
 ("Stefan Ihmig","RE:SORB","info@resorb.tv","general","resorb.tv","Founder/Media Artist RE:SORB Berlin + Tbilisi. Hook: Art Vision Classic 2019 (1. Preis, Bolshoi), Festival of Lights Fernsehturm 2022, Sharjah Light Festival 2023-26."),
 ("Brad Hurle","Diverse AV","production@diverseav.com.au","general","diverseav.com.au, taitt.com.au/testimonials","Owner/MD Diverse AV, Pakenham (Melbourne). Hook: Hilltop Hoods 'Great Expanse' Tour, Monster Energy Tours, @roadies_who_cook (TPi Magazine)."),
 ("Guillem","Mago Pop","","general","teatrevictoria.com","Kein technisches Personal oeffentlich. Nur Theater-Support suport@teatrevictoria.com (schwach). Hook: 'Nada es imposible' im Teatre Victoria bis Mai 2026, Stadiontour ab 2027 (Bernabeu bis Camp Nou)."),
 ("Jose Lopez de Paula","Mago Pop","","general","teatrevictoria.com","Siehe Guillem. Kontakt am besten ueber bestehenden VIOSO-Kontakt."),
 ("Matteo","Epson","","general","installation-international.com (ISE 2026), press.epson.eu","Kein 'Matteo' oeffentlich dokumentiert. Dokumentierte Epson-Europe-Projektor-Kontakte: Massimo Pizzocri (VP Video Projector Sales), Daniel Rose (PM Video Projection), Graeme Davidson (Director VI Business)."),
 ("Maarten van Sloten","Specialelektronik","info@specialelektronik.se","general","specialelektronik.se","Special-Elektronik AB, schwedischer Pro-AV-Distributor (Karlstad). Person nicht auf der Site genannt."),
 ("Andre Bauer","M2 Projects","","general","","Online nicht auffindbar (m2projects.de leer). Schreibweise/Firma pruefen."),
 ("Sebastian Geenz","Kontakt pruefen","","general","","Online nicht auffindbar, vermutlich Schreibweise (Genz?). Bitte klaeren."),
 ("Dustin Mueller","studio : 3","","general","","Online nicht auffindbar (studio-3.de ist ein Muenchner Fotostudio). Richtige Domain/Firma pruefen."),
 ("Fedor Stuhrmann","studio : 3","","general","","Siehe Dustin Mueller."),
 ("Misha","L&F","","general","","Firma L&F nicht identifizierbar. Bitte vollen Namen/Firma ergaenzen."),
 ("Tomás Saragaço","Independent media engineer","","general","","Keine oeffentliche Spur (auch PT-Suche). Direktkontakt notwendig."),
 ("Rossi TC Chou","BenQ","","general","","Nur BenQ-Patentinhaber 'Tung-Chia Chou' (Projektor-Patente) auffindbar, keine Rolle oeffentlich."),
 ("Ben Moors","BenQ","","general","","Keine oeffentliche Adresse. Hook: BenQ Benelux Projection-Mapping/ProAV-Event Rotterdam."),
 ("Christian Kuntze","Sigma","","general","sigma-av.com/ueber-uns","Teamseite nennt nur 'Christian K.'. GF: Marco Vorderstemann, Stephan Nabbefeld. Hook: Drohnenshow XPONENTIAL Europe, 'In Motion' Deutsches Fussball Museum. Gleiche Stadt wie VIOSO."),
 ("Andreas Schulze","inSynergie","","general","insynergie.de/impressum","Geschaeftsfuehrer bestaetigt. Hook: 'Immersive Sky' Therme Euskirchen, Klimahaus Bremerhaven, Forum Wissen Goettingen, experimenta Heilbronn."),
 ("Tobias Mayer","satis&fy","","general","satis-fy.com/news","Hook: Purple Disco Machine im Dresdner Zwinger 2026, AYMO Arena Tour 2026, BrandEx Award 2026, World of Hans Zimmer."),
 ("Daniel Seeger","Neumann & Mueller","","general","neumannmueller.com/en/video","Hook: Facade Mapping Memmingen, Porsche Tennis Grand Prix 2024, 150 Jahre Bayer; 45 Jahre N&M 2026."),
]
# Placeholder rows ('Technischer Lead') where research found a named technical contact.
# Only renamed while the row still carries the placeholder name.
PROPOSED_LEADS=[
 ("Virtuality.one","David Houzvicka","david.houzvicka@virtuality.one","virtuality.one/hire-us","Technical Director, Virtuality.one Prag (CZ, nicht DE). Pixera/Unreal/ROE LED Virtual-Production-Studio. Hook: 'Civilisations: Rise and Fall' (BBC 2025), 'Signal Space 2025' Mapping + Server-Integration."),
 ("Videlio","Vincent Varoquier","","sportsvideo.org (Riedel, 03/2025), videlio.com","Technical Director Videlio Events, Gennevilliers. Nur Kontaktformular. Hook: drei Flyaway-Video-Regien auf Riedel MediorNet HorizoN/MicroN UHD."),
 ("VIDEMUS","Benoit Dauvergne","","videmus.fr/a-propos","President VIDEMUS SAS, Cachan. Distributor fuer Dataton WATCHOUT, PIXILAB Blocks, BlackTrax, Medialon. Allgemeine Adresse info@videmus.fr bleibt."),
 ("pixel.formation","Peter Lynn","","pixelformation.com/team","Director/Technical Director. Achtung: australische Firma (Brisbane/Sydney/Melbourne) mit Berliner Praesenz, nur Kontaktformular. Merger aus Twisted Pixel + FORMATION."),
 ("Ktech Media Solutions","","","ktechmediasolutions.com","Achtung: einzige Firma dieses Namens sitzt in Mumbai (Digital-Marketing + WATCHOUT), keine UK-Firma gefunden. Zuordnung pruefen."),
 ("ADSI","","","adsi.fr","Achtung: adsi.fr ist nur eine Platzhalterseite, keine AV-Firma 'ADSI' in FR gefunden. Zuordnung pruefen."),
]
def conn():
 c=sqlite3.connect(DB,timeout=20);c.row_factory=sqlite3.Row;c.execute("PRAGMA busy_timeout=20000");return c
def init():
 with lock,conn() as c:
  c.execute("PRAGMA journal_mode=WAL")
  c.execute("""CREATE TABLE IF NOT EXISTS guests(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,company TEXT NOT NULL,country TEXT DEFAULT '',email TEXT DEFAULT '',role TEXT DEFAULT '',priority TEXT DEFAULT 'B',decision TEXT DEFAULT 'Offen',owner TEXT DEFAULT '',invitation TEXT DEFAULT '',done INTEGER DEFAULT 0,feedback TEXT DEFAULT '',rsvp TEXT DEFAULT 'Offen',hotel TEXT DEFAULT '',food TEXT DEFAULT '',plus_one TEXT DEFAULT '',notes TEXT DEFAULT '',updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
  if "rating" not in [r[1] for r in c.execute("PRAGMA table_info(guests)")]:
   c.execute("ALTER TABLE guests ADD COLUMN rating INTEGER DEFAULT 0")
  if c.execute("SELECT COUNT(*) FROM guests").fetchone()[0]==0:
   for s in SEEDS:
    c.execute("INSERT INTO guests(name,company,country,email,notes) VALUES(?,?,?,?,?)",(s[0],s[1],s[2],s[3] if len(s)>3 else "","Bring an additional technical colleague if useful" if s[0] in ("Andreas Schulze","Tobias Mayer","Christian Kuntze","Daniel Seeger") else ""))

  # Backfill only empty contact details. Existing team changes always win.
  verified_contacts=[
   ("Christian Kuntze","Sigma","ck@sigma-av.com"),
   ("Andreas Schulze","inSynergie","schulze@insynergie.de"),
   ("Tobias Mayer","satis&fy","TobiasMayer@satis-fy.com"),
   ("Daniel Seeger","Neumann & Mueller","Daniel.Seeger@neumannmueller.com"),
   ("Sven Fischer","Project Syntropy","fischer@project-syntropy.de"),
   ("Alexandre Willame","Trio-Tech","a.willame@trio-tech.com"),
   ("John Mould","ST Engineering Antycip","John.Mould@steantycip.com"),
   ("Vangelis Petridis","Omikron","petridis@omikron.gr"),
   ("Simon Reed","Beyond Light","simonr@lightfield.london"),
   ("Morgan Wong","Dataton-Umfeld","watchoutmorgan@gmail.com"),
   ("Dimitris","Omikron","mastrokolias@omikron.gr"),
   ("David Butler","Pixsper","info@pixsper.com"),
   ("Noemie Waterlot","VIDEMUS","info@videmus.fr")
  ]
  for name,company,email in verified_contacts:
   c.execute("UPDATE guests SET email=? WHERE name=? AND company=? AND (email IS NULL OR TRIM(email)='')",(email,name,company))
  c.execute("UPDATE guests SET name='Dimitris Mastrokolias' WHERE name='Dimitris' AND company='Omikron'")

  # Corrections with clear public evidence. Applied only while the row still has the seed value.
  c.execute("UPDATE guests SET name='Florian Miodek' WHERE name='Fabian Miodek' AND company='Aufwind'")
  c.execute("UPDATE guests SET country='CZ' WHERE company='Virtuality.one' AND country='DE'")
  c.execute("UPDATE guests SET country='AU' WHERE company='pixel.formation' AND country='DE'")
  c.execute("UPDATE guests SET country='SE' WHERE company='Specialelektronik' AND country='NL'")
  c.execute("DELETE FROM guests WHERE name='Michael Mueller' AND company='HAMACO-Umfeld'")

  # Proposed contacts from public web research. Only fill EMPTY e-mail fields and add a
  # "Vorschlag" note with the source so the team can verify before inviting. Never overwrite.
  # Tuple: (name, company, email, kind, source_url, extra_note)
  for name,company,email,kind,source,extra in PROPOSED_CONTACTS:
   row=c.execute("SELECT id,email,notes FROM guests WHERE name=? AND company=?",(name,company)).fetchone()
   if not row:continue
   label=("allgemeine Firmenadresse" if kind=="general" else "öffentlich gelistet") if email else "Recherche"
   note=("Vorschlag ("+label+(", Quelle: "+source if source else "")+"), bitte prüfen."+(" "+extra if extra else "")).strip()
   if email and not (row["email"] or "").strip():
    c.execute("UPDATE guests SET email=? WHERE id=?",(email,row["id"]))
   if "Vorschlag (" not in (row["notes"] or "") and (email or extra):
    c.execute("UPDATE guests SET notes=? WHERE id=?",(((row["notes"] or "").strip()+"\n"+note).strip(),row["id"]))
  for company,person,email,source,extra in PROPOSED_LEADS:
   row=c.execute("SELECT id,name,email,notes FROM guests WHERE company=? AND name='Technischer Lead'",(company,)).fetchone()
   if not row:continue
   if person:c.execute("UPDATE guests SET name=? WHERE id=?",(person,row["id"]))
   if email and not (row["email"] or "").strip():c.execute("UPDATE guests SET email=? WHERE id=?",(email,row["id"]))
   note="Vorschlag (oeffentlich gelistet, Quelle: "+source+"), bitte pruefen. "+extra
   if "Vorschlag (" not in (row["notes"] or ""):c.execute("UPDATE guests SET notes=? WHERE id=?",(((row["notes"] or "").strip()+"\n"+note).strip(),row["id"]))
  c.execute("UPDATE guests SET notes=CASE WHEN TRIM(COALESCE(notes,''))='' THEN ? ELSE notes END WHERE name=? AND company=?",("General company address (not personal); confirm direct contact before inviting","David Butler","Pixsper"))
  c.execute("UPDATE guests SET notes=CASE WHEN TRIM(COALESCE(notes,''))='' THEN ? ELSE notes END WHERE name=? AND company=?",("General VIDEMUS address; WATCHOUT Academy takes place Dec 9–10, check availability","Noemie Waterlot","VIDEMUS"))
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
   if k=="rating":
    if isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=5:raise ValueError("Invalid rating")
   elif k=="done":
    if not isinstance(v,(bool,int)):raise ValueError("Invalid done")
   elif not isinstance(v,str) or len(v)>12000:raise ValueError("Invalid text")
  if "decision" in obj and obj["decision"] not in ("Ja","Nein","Offen"):raise ValueError("Invalid decision")
  if "rsvp" in obj and obj["rsvp"] not in ("Offen","Zusage","Absage","Vielleicht"):raise ValueError("Invalid RSVP")
  return obj
 def static(self,path):
  # Public assets: only plain file names inside ./static, no sub paths or traversal.
  name=path[len("/static/"):]
  f=STATIC/name
  if "/" in name or name.startswith(".") or f.suffix not in STATIC_TYPES or not f.is_file():return self.out(404,{"error":"Not found"})
  b=f.read_bytes()
  self.send_response(200);self.send_header("Content-Type",STATIC_TYPES[f.suffix]);self.send_header("Cache-Control","public, max-age=3600");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  path=urlparse(self.path).path
  if path=="/api/health":return self.out(200,{"ok":True})
  # Public: the invitation page is linked from the e-mails sent to guests, so it must open without a login.
  if path.startswith("/static/"):return self.static(path)
  if path=="/favicon.ico":return self.static("/static/favicon.svg")
  if path in ("/event","/event/","/event.html"):return self.out(200,(ROOT/"event.html").read_bytes(),"text/html; charset=utf-8")
  # Everything below (guest list and API) stays behind Basic Auth.
  if not self.auth():return
  if path=="/api/guests":
   with lock,conn() as c: rows=[dict(x) for x in c.execute("SELECT * FROM guests ORDER BY id")]
   return self.out(200,rows)
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
