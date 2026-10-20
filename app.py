import streamlit as st
import streamlit.components.v1 as components
import sqlite3, secrets, io, html, os, base64, calendar, re
import pandas as pd
from datetime import datetime, date
from urllib.parse import quote

# ================= CONFIGURA AQUÍ =================
NOVIOS = "Steven & Emely"
EMOJI = "💍"
TITULO_EVENTO = "¡Nos casamos!"
SUBTITULO = "Queremos compartir este día tan especial contigo"
FECHA_TEXTO = "Sábado 28 de noviembre de 2026"
FECHA_ISO = date(2026, 11, 28)          # año-mes-día (para la cuenta regresiva)

MISA_HORA = "4:00 p. m."
MISA_LUGAR = "Iglesia de Tobo"
MISA_MAPA = "Iglesia de Tobo"            # texto que busca Google Maps

FIESTA_HORA = "6:00 p. m."
FIESTA_LUGAR = "Rancho California (antiguamente Manpower)"
FIESTA_MAPA = "Rancho California Manpower"
FIESTA_MAPA_URL = "https://share.google/xR3GdcnH2byiwOrnk"   # enlace exacto de Google Maps (si está, se usa en vez de la búsqueda)
MISA_MAPA_URL = ""                                           # opcional: enlace exacto de la iglesia

MENSAJE = "Gracias por ser parte de nuestra historia. ¡Te esperamos!"
VESTIMENTA = "Libre"   # déjalo vacío ("") para no mostrarlo
EXTRAS = "🍖 Asado · 🎺 Orquesta · 🎧 DJ"   # lo que habrá en la fiesta; vacío ("") para ocultar
CONTACTOS = ["3214569187", "3213059268"]   # para dudas
FRASE = "Entre tantos caminos, el amor nos encontró. Hoy empieza nuestro para siempre."   # sale en "Nuestra historia"; vacío ("") para ocultar
# --- Fotos (carpeta "fotos" junto a este archivo) ---
FOTO_PORTADA = "foto4.jpg"   # la que se ve grande arriba
FOTOS = ["foto1.jpg", "foto2.jpg", "foto3.jpg", "foto4.jpg", "foto5.jpg", "foto6.jpg"]

# --- Itinerario del día (ajusta las horas de lo que no sea misa/recepción) ---
ITINERARIO = [
    ("⛪", MISA_HORA, "Misa", MISA_LUGAR),
    ("🥂", FIESTA_HORA, "Recepción", FIESTA_LUGAR),
    ("📸", "7:00 p. m.", "Fotos y vals", "Los novios abren la pista"),
    ("🍽️", "8:00 p. m.", "Comida", "Asado para todos"),
    ("🎉", "9:00 p. m.", "Fiesta", "Orquesta y DJ hasta que el cuerpo aguante"),
]
HORA_MISA_ISO = "16:00:00-05:00"   # para la cuenta regresiva (hora de Colombia)

MUSICA = "musica.mp3"   # archivo en la misma carpeta; vacío ("") para quitar la música
CLAVE_ADMIN = os.environ.get("CLAVE_ADMIN", "cambia-esta-clave")  # ¡CÁMBIALA!
DB = os.environ.get("DB_PATH", "invitacion.db")   # en el hosting se usa un disco persistente
AUTOSCROLL = True        # la invitación baja sola después de abrir el sobre (el invitado puede pausarla)
VELOCIDAD_AUTO = 50      # píxeles por segundo: más bajo = más lento
# ===================================================

ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Pinyon+Script&display=swap');
.stApp{background-color:#f6f0e6;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/><feColorMatrix values='0 0 0 0 .55 0 0 0 0 .42 0 0 0 0 .25 0 0 0 .07 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");}
.stApp, .stApp p, .stApp label{font-family:'Cormorant Garamond',Georgia,serif;}
.sec{max-width:600px;margin:40px auto 14px;text-align:center;font-family:'Cormorant Garamond',Georgia,serif;
font-size:36px;font-weight:600;color:#3b1520}
.sec:after{content:"";display:block;width:60px;height:1px;background:#b08d57;margin:10px auto 0}
.tl{max-width:560px;margin:0 auto;padding:6px 0 6px 0;position:relative;font-family:'Cormorant Garamond',Georgia,serif}
.tl:before{content:"";position:absolute;left:104px;top:18px;bottom:18px;width:1px;background:#c7a76b}
.tl .it{display:grid;grid-template-columns:92px 26px 1fr;align-items:start;margin:0 0 22px}
.tl .h{text-align:right;font-size:19px;font-weight:700;color:#6e2433;padding-top:2px}
.tl .p{width:13px;height:13px;border-radius:50%;background:#f6f0e6;border:2px solid #b08d57;margin:8px 0 0 7px;position:relative;z-index:1}
.tl .d{padding-left:6px}
.tl .d b{display:block;font-size:25px;color:#3b1520;font-weight:600}
.tl .d span{font-size:18px;color:#6d5d4c;font-style:italic}
.lugar{max-width:560px;margin:0 auto 12px;background:#fffdf9;border:1px solid #e3d2ac;padding:16px 20px;text-align:center;
font-family:'Cormorant Garamond',Georgia,serif;color:#2b2523}
.lugar .t{font-size:17px;font-style:italic;color:#8a6d2b}
.lugar .h{font-size:28px;font-weight:700;color:#3b1520;line-height:1.2}
.lugar .l{font-size:20px}
.nota{max-width:560px;margin:14px auto;padding:16px 20px;text-align:center;font-size:20px;line-height:1.45;
font-family:'Cormorant Garamond',Georgia,serif;color:#3b2f2a;background:#f1e7d6;border:1px dashed #b08d57}
.nota.msg{background:none;border:none;font-style:italic;font-size:22px;color:#6e2433}
.pase{max-width:420px;margin:14px auto;overflow:hidden;background:#fffdf9;border:1px solid #c7a76b;outline:1px solid #e3d2ac;
outline-offset:5px;font-family:'Cormorant Garamond',Georgia,serif;text-align:center;box-shadow:0 10px 28px rgba(70,40,30,.18)}
.pase .top{background:#6e2433;color:#fff;padding:10px;letter-spacing:3px;font-size:15px;text-transform:uppercase}
.pase .cuerpo{padding:14px 10px;color:#2b2523;font-size:19px}
.pase .n{font-size:36px;font-weight:700;color:#3b1520;line-height:1.15}
.pase .corte{border-top:2px dashed #c9a24b;margin:0 14px}
.pase .abajo{padding:10px;font-size:17px;color:#6d5d4c}
.stApp{color-scheme:light}
[data-testid="stForm"]{background:#fffdf9;border:1px solid #c7a76b;border-radius:2px;padding:18px 20px}
[data-testid="stForm"] label,[data-testid="stForm"] p,[data-testid="stForm"] span,[data-testid="stForm"] div,
[data-testid="stWidgetLabel"] *{color:#2b2523!important}
[data-testid="stForm"] [data-baseweb="input"],[data-testid="stForm"] [data-baseweb="base-input"],
[data-testid="stForm"] [data-baseweb="textarea"]{background:#fff!important;border-color:#c7a76b!important}
[data-testid="stForm"] input,[data-testid="stForm"] textarea{background:#fff!important;color:#2b2523!important;
-webkit-text-fill-color:#2b2523!important;caret-color:#6e2433}
[data-testid="stForm"] [data-testid="stNumberInputStepDown"],[data-testid="stForm"] [data-testid="stNumberInputStepUp"]{
background:#efe6d6!important;color:#2b2523!important}
[data-testid="stForm"] [data-testid="stNumberInputStepDown"] *,[data-testid="stForm"] [data-testid="stNumberInputStepUp"] *{color:#2b2523!important}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button{background:#6e2433!important;border:1px solid #c7a76b!important}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button *{color:#fff!important}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:#6d5d4c!important}
.frase{max-width:520px;margin:6px auto 26px;padding:0 18px;text-align:center;font-family:'Pinyon Script',cursive;
font-size:34px;line-height:1.3;color:#9c7a3f}
.frase:before,.frase:after{content:"";display:block;width:70px;height:1px;background:#c7a76b;margin:12px auto}
.frase .cm{font-family:'Cormorant Garamond',Georgia,serif;font-size:54px;line-height:0;color:#c7a76b;vertical-align:-14px;margin:0 4px}
@media (max-width:480px){.frase{font-size:28px}}
@keyframes aparece{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:none}}
@supports (animation-timeline:view()){
.sec,.lugar,.nota,.frase,.tl .it,.pase{animation:aparece linear both;animation-timeline:view();animation-range:entry 0% entry 55%}
}
@media (prefers-reduced-motion:reduce){.sec,.lugar,.nota,.frase,.tl .it,.pase{animation:none!important}}
</style>
"""


def con():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def iniciar():
    with con() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS invitados(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Pendiente',
            acompanantes INTEGER NOT NULL DEFAULT 0,
            mensaje TEXT DEFAULT '',
            fecha_respuesta TEXT)""")
        try:
            c.execute("ALTER TABLE invitados ADD COLUMN telefono TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # la columna ya existe


def maps(q):
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def archivo_calendario():
    f = FECHA_ISO.strftime("%Y%m%d")
    return (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Invitacion//ES\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:misa-{f}@invitacion\r\nSUMMARY:Misa - Boda {NOVIOS}\r\n"
        f"DTSTART;TZID=America/Bogota:{f}T160000\r\nDTEND;TZID=America/Bogota:{f}T173000\r\n"
        f"LOCATION:{MISA_LUGAR}\r\nEND:VEVENT\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:fiesta-{f}@invitacion\r\nSUMMARY:Celebración - Boda {NOVIOS}\r\n"
        f"DTSTART;TZID=America/Bogota:{f}T180000\r\nDTEND;TZID=America/Bogota:{f}T235900\r\n"
        f"LOCATION:{FIESTA_LUGAR}\r\nEND:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


@st.cache_data
def foto_uri(nombre):
    base = os.path.dirname(os.path.abspath(__file__))
    ruta = next((r for r in (os.path.join(base, "fotos", nombre), os.path.join(base, nombre))
                 if os.path.exists(r)), None)
    if not ruta:
        return ""
    with open(ruta, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


IFRAME_BASE = """
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{margin:0;background:transparent;font-family:'Cormorant Garamond',Georgia,serif;color:#2b2523;text-align:center}
@keyframes lat{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.14)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""

MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
CORAZON = ('<svg viewBox="0 0 24 24"><path d="M12 21s-7.5-4.6-9.6-9.2C.8 8.2 3 4.5 6.6 4.5c2 0 3.5 1.1 4.4 2.6'
           '.9-1.5 2.4-2.6 4.4-2.6 3.6 0 5.8 3.7 4.2 7.3C19.5 16.4 12 21 12 21z"/></svg>')


def calendario_html():
    cal = calendar.Calendar(firstweekday=6)  # semana empieza en domingo
    filas = ""
    for semana in cal.monthdayscalendar(FECHA_ISO.year, FECHA_ISO.month):
        celdas = ""
        for d in semana:
            if d == 0:
                celdas += "<td></td>"
            elif d == FECHA_ISO.day:
                celdas += f'<td class="sel">{CORAZON}<span>{d}</span></td>'
            else:
                celdas += f"<td><span>{d}</span></td>"
        filas += f"<tr>{celdas}</tr>"
    return (f'<div class="mes">{MESES[FECHA_ISO.month]} {FECHA_ISO.year}</div>'
            '<table><tr><th>D</th><th>L</th><th>M</th><th>M</th><th>J</th><th>V</th><th>S</th></tr>'
            f'{filas}</table>')


def bloque_cuenta_y_calendario():
    destino = f"{FECHA_ISO.isoformat()}T{HORA_MISA_ISO}"
    page = IFRAME_BASE + """
.cd{display:flex;justify-content:center;gap:10px;margin:4px 0 26px}
.cd div{width:76px;padding:12px 0 10px;background:#6e2433;color:#fff;border:1px solid #c7a76b;outline:1px solid #6e2433;outline-offset:3px}
.cd b{display:block;font-size:34px;line-height:1;font-weight:700}
.cd span{font-size:15px;font-style:italic;opacity:.9}
.hoy{font-size:30px;font-weight:700;color:#6e2433;margin:10px 0 26px}
.cal{max-width:400px;margin:0 auto;background:#fffdf9;border:1px solid #e3d2ac;padding:16px 12px 12px}
.mes{font-size:28px;font-weight:700;color:#3b1520;margin-bottom:8px}
table{width:100%;border-collapse:collapse;table-layout:fixed}
th{font-size:16px;color:#8a6d2b;font-weight:600;padding:4px 0 8px}
td{position:relative;height:44px;font-size:20px;color:#4a3d36;padding:0}
td span{position:relative;z-index:1}
td.sel svg{position:absolute;left:50%;top:50%;width:42px;height:42px;fill:#d9b48a;transform:translate(-50%,-50%);
animation:lat 1.8s ease-in-out infinite;filter:drop-shadow(0 2px 3px rgba(120,80,40,.35))}
td.sel span{font-weight:700;color:#3b2615;font-size:19px;margin-top:-2px;display:inline-block}
.sub{font-size:19px;font-style:italic;color:#6d5d4c;margin:12px 0 0}
</style>
<div class="cd" id="cd">
 <div><b id="d">--</b><span>días</span></div><div><b id="h">--</b><span>horas</span></div>
 <div><b id="m">--</b><span>min</span></div><div><b id="s">--</b><span>seg</span></div>
</div>
<div class="cal">__CAL__<p class="sub">Guarda la fecha: te esperamos</p></div>
<script>
const t=new Date("__DESTINO__").getTime();
function z(n){return String(n).padStart(2,'0')}
function tick(){
  let r=t-Date.now();
  if(r<=0){document.getElementById('cd').outerHTML='<div class="hoy">¡Hoy es el gran día! 🎉</div>';return}
  const d=Math.floor(r/864e5),h=Math.floor(r%864e5/36e5),m=Math.floor(r%36e5/6e4),s=Math.floor(r%6e4/1e3);
  document.getElementById('d').textContent=d;document.getElementById('h').textContent=z(h);
  document.getElementById('m').textContent=z(m);document.getElementById('s').textContent=z(s);
}
tick();setInterval(tick,1000);
</script>"""
    page = page.replace("__CAL__", calendario_html()).replace("__DESTINO__", destino)
    components.html(page, height=560)


def bloque_galeria():
    imgs = [foto_uri(n) for n in FOTOS]
    imgs = [u for u in imgs if u]
    if not imgs:
        return
    thumbs = "".join(f'<img src="{u}" alt="Foto {k + 1}">' for k, u in enumerate(imgs))
    page = IFRAME_BASE + """
.vista{position:relative;height:430px;background:#fffdf9;border:1px solid #e3d2ac;display:flex;align-items:center;justify-content:center;cursor:zoom-in;overflow:hidden}
.vista img{max-width:100%;max-height:100%;object-fit:contain;transition:opacity .35s}
.fl{position:absolute;top:50%;transform:translateY(-50%);width:42px;height:42px;border-radius:50%;border:1px solid #c7a76b;
background:rgba(255,253,249,.88);color:#6e2433;font-size:22px;cursor:pointer;line-height:1}
.fl.a{left:8px}.fl.b{right:8px}
.fl:focus-visible,.th img:focus-visible{outline:2px solid #6e2433}
.cnt{position:absolute;bottom:8px;right:12px;font-size:16px;color:#6d5d4c;background:rgba(255,253,249,.85);padding:1px 10px}
.th{display:flex;gap:8px;justify-content:center;margin-top:10px;flex-wrap:wrap}
.th img{width:58px;height:58px;object-fit:cover;cursor:pointer;opacity:.55;border:2px solid transparent;transition:opacity .2s}
.th img.on{opacity:1;border-color:#b08d57}
.lb{position:fixed;inset:0;background:rgba(30,15,18,.93);display:none;align-items:center;justify-content:center;z-index:9}
.lb.on{display:flex}
.lb img{max-width:94%;max-height:92%}
.lb .x{position:absolute;top:10px;right:14px;color:#fff;font-size:34px;cursor:pointer;background:none;border:none}
.lb .fl{background:rgba(255,255,255,.18);color:#fff;border-color:rgba(255,255,255,.4)}
</style>
<div class="vista" id="v"><img id="big" alt="Foto de los novios"><button class="fl a" id="pa" aria-label="Anterior">‹</button>
<button class="fl b" id="pb" aria-label="Siguiente">›</button><div class="cnt" id="c"></div></div>
<div class="th" id="th">__THUMBS__</div>
<div class="lb" id="lb"><button class="x" id="x" aria-label="Cerrar">×</button><button class="fl a" id="la">‹</button>
<img id="lbi" alt=""><button class="fl b" id="lbb">›</button></div>
<script>
const T=[...document.querySelectorAll('#th img')],big=document.getElementById('big'),lb=document.getElementById('lb'),lbi=document.getElementById('lbi');
let i=0,auto=setInterval(()=>go(i+1),5000);
function stop(){clearInterval(auto)}
function go(n){i=(n+T.length)%T.length;big.style.opacity=0;setTimeout(()=>{big.src=T[i].src;big.style.opacity=1},120);
  T.forEach((e,k)=>e.classList.toggle('on',k==i));document.getElementById('c').textContent=(i+1)+' / '+T.length;
  if(lb.classList.contains('on'))lbi.src=T[i].src}
T.forEach((e,k)=>e.onclick=()=>{stop();go(k)});
document.getElementById('pa').onclick=ev=>{ev.stopPropagation();stop();go(i-1)};
document.getElementById('pb').onclick=ev=>{ev.stopPropagation();stop();go(i+1)};
document.getElementById('la').onclick=()=>go(i-1);document.getElementById('lbb').onclick=()=>go(i+1);
document.getElementById('v').onclick=()=>{stop();lbi.src=T[i].src;lb.classList.add('on')};
document.getElementById('x').onclick=()=>lb.classList.remove('on');
lb.onclick=ev=>{if(ev.target===lb)lb.classList.remove('on')};
document.addEventListener('keydown',ev=>{if(ev.key==='ArrowLeft')go(i-1);if(ev.key==='ArrowRight')go(i+1);if(ev.key==='Escape')lb.classList.remove('on')});
let x0=null;
for(const el of [document.getElementById('v'),lb]){
  el.addEventListener('touchstart',e=>{x0=e.touches[0].clientX},{passive:true});
  el.addEventListener('touchend',e=>{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0;
    if(Math.abs(dx)>40){stop();go(i+(dx<0?1:-1))}x0=null},{passive:true});
}
big.src=T[0].src;T[0].classList.add('on');document.getElementById('c').textContent='1 / '+T.length;
</script>"""
    components.html(page.replace("__THUMBS__", thumbs), height=540)


def itinerario_html():
    items = ""
    for emoji, hora, titulo, detalle in ITINERARIO:
        det = f"<span>{html.escape(detalle)}</span>" if detalle else ""
        items += (f'<div class="it"><div class="h">{html.escape(hora)}</div><div class="p"></div>'
                  f'<div class="d"><b>{emoji} {html.escape(titulo)}</b>{det}</div></div>')
    return f'<div class="tl">{items}</div>'


ALTO_SOBRE = 700   # alto del recuadro del sobre (se ajusta solo al abrir)

SOBRE_HTML = """
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Pinyon+Script&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
html,body{margin:0;background:transparent;font-family:'Cormorant Garamond',Georgia,serif;color:#2b2523;overflow-x:hidden}
button{font-family:inherit}

/* ---------- ESCENARIO DEL SOBRE ---------- */
.stage{position:relative;height:__ALTO__px;display:flex;align-items:center;justify-content:center;
 background:radial-gradient(ellipse 62% 46% at 50% 50%,rgba(255,250,238,.95),rgba(255,250,238,0) 72%);
 transition:opacity .9s ease,transform .9s ease}
.stage.fuera{opacity:0;transform:scale(1.12);pointer-events:none}
.tit{position:absolute;top:46px;left:0;right:0;text-align:center;transition:opacity .6s}
.tit small{display:block;font-size:20px;font-style:italic;color:#8a6d2b;letter-spacing:.5px}
.tit b{display:block;font-family:'Pinyon Script',cursive;font-weight:400;font-size:48px;color:#6e2433;line-height:1.2;margin-top:2px}
.hint{position:absolute;bottom:56px;left:0;right:0;text-align:center;font-size:21px;font-style:italic;color:#7a6a58;
 animation:pulso 2.2s ease-in-out infinite;transition:opacity .5s}
@keyframes pulso{0%,100%{opacity:.55;transform:translateY(0)}50%{opacity:1;transform:translateY(-4px)}}
.sp{position:absolute;width:5px;height:5px;background:#d9b86a;border-radius:50%;opacity:0;animation:brilla 3.4s ease-in-out infinite;
 box-shadow:0 0 6px 2px rgba(217,184,106,.55)}
@keyframes brilla{0%,100%{opacity:0;transform:scale(.4) translateY(0)}50%{opacity:.95;transform:scale(1) translateY(-14px)}}

.escena{transform-origin:50% 50%}
.bob{animation:bob 4.2s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-.6deg)}50%{transform:translateY(-9px) rotate(.6deg)}}

.env{position:relative;width:340px;height:230px;perspective:1100px;cursor:pointer}
.back{position:absolute;inset:0;z-index:0;border-radius:3px;background:linear-gradient(180deg,#c9ae84,#d6bf99);
 box-shadow:0 20px 40px rgba(70,40,30,.25)}

/* solapa (se abre en 3D) */
.flap{position:absolute;left:0;top:0;width:100%;height:55%;z-index:4;transform-origin:50% 0;transform-style:preserve-3d;
 transition:transform .95s cubic-bezier(.5,0,.25,1)}
.flap .o,.flap .i{position:absolute;inset:0;clip-path:polygon(0 0,100% 0,50% 100%);backface-visibility:hidden;-webkit-backface-visibility:hidden}
.flap .o{background:linear-gradient(180deg,#dbc59c,#cdb28a)}
.flap .i{transform:rotateX(180deg);
 background:linear-gradient(135deg,rgba(176,141,87,.25) 25%,transparent 25%) -8px 0/16px 16px,
            linear-gradient(225deg,rgba(176,141,87,.25) 25%,transparent 25%) -8px 0/16px 16px,#efe3cc}
.env.abre .flap{transform:rotateX(180deg)}
.env.atras .flap{z-index:1}

/* tarjetita que sale del sobre */
.mini{position:absolute;left:20px;top:14px;width:300px;height:206px;z-index:2;background:#fffaf0;border:1px solid #c7a76b;
 outline:1px solid #e3d2ac;outline-offset:-6px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;
 transition:transform 1.1s cubic-bezier(.22,.9,.3,1),box-shadow 1s}
.mini .m1{font-size:16px;font-style:italic;color:#8a6d2b}
.mini .m2{font-family:'Pinyon Script',cursive;font-size:42px;color:#9c7a3f;line-height:1.15}
.mini .m3{font-size:14px;letter-spacing:7px;color:#b08d57;margin-top:2px}
.env.sale .mini{transform:translateY(-150px)}
.env.frente .mini{z-index:5;transform:translateY(-205px) scale(1.1);box-shadow:0 22px 44px rgba(70,40,30,.28)}

/* bolsillo (frente del sobre) */
.bolsillo{position:absolute;inset:0;z-index:3;filter:drop-shadow(0 -2px 3px rgba(70,40,30,.2))}
.bolsillo i{position:absolute;inset:0;display:block}
.bolsillo .l{clip-path:polygon(0 0,0 100%,50% 55%);background:linear-gradient(100deg,#e6d5b6,#d8c39c)}
.bolsillo .r{clip-path:polygon(100% 0,100% 100%,50% 55%);background:linear-gradient(260deg,#e6d5b6,#d8c39c)}
.bolsillo .b{clip-path:polygon(0 100%,50% 55%,100% 100%);background:linear-gradient(180deg,#ecdcbd,#e1cda8)}
.para{position:absolute;left:0;right:0;bottom:20px;z-index:4;text-align:center;line-height:1.1;pointer-events:none}
.para small{display:block;font-size:13px;letter-spacing:4px;text-transform:uppercase;color:#8a6d2b}
.para b{display:block;font-family:'Pinyon Script',cursive;font-weight:400;font-size:32px;color:#6e2433;white-space:nowrap}

/* sello de cera */
.seal{position:absolute;left:50%;top:55%;width:64px;height:64px;margin:-32px 0 0 -32px;z-index:6;border:none;cursor:pointer;
 border-radius:50% 46% 52% 48% / 48% 52% 46% 50%;
 background:radial-gradient(circle at 35% 30%,#a8405a,#6e2433 60%,#4a1220);
 box-shadow:0 5px 12px rgba(40,10,20,.5),inset 0 0 0 3px rgba(227,210,172,.35),inset 0 0 0 5px rgba(0,0,0,.12);
 color:#f3dfae;font-size:19px;font-style:italic;font-weight:700;letter-spacing:.5px;
 transition:transform .35s,opacity .35s;animation:latido 1.9s ease-in-out infinite}
.seal:before{content:"";position:absolute;inset:-7px;border-radius:50%;border:1px solid rgba(110,36,51,.45);animation:onda 1.9s ease-out infinite}
@keyframes latido{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}
@keyframes onda{0%{transform:scale(.9);opacity:.8}100%{transform:scale(1.55);opacity:0}}
.seal:focus-visible{outline:2px solid #6e2433;outline-offset:5px}
.env.rompe .seal{animation:none;transform:scale(1.3) rotate(9deg);opacity:0;pointer-events:none}
.env.rompe .seal:before{display:none}
.ch{position:absolute;left:50%;top:55%;width:6px;height:6px;margin:-3px;border-radius:50%;background:#e0bf72;z-index:7;
 pointer-events:none;box-shadow:0 0 6px 2px rgba(224,191,114,.7)}

/* ---------- LA INVITACIÓN ---------- */
.inv{display:none;position:relative;padding:16px 14px 28px}
.inv.on{display:block}
.tarjeta{position:relative;max-width:560px;margin:0 auto;background:#fffdf9;border:1px solid #c7a76b;outline:1px solid #e3d2ac;
 outline-offset:6px;overflow:hidden;box-shadow:0 22px 50px rgba(70,40,30,.2);
 transform:translateY(70px) scale(.9);opacity:0;transition:transform 1.1s cubic-bezier(.2,.9,.25,1),opacity .9s}
.inv.on .tarjeta{transform:none;opacity:1}
.tarjeta.listo{transition:transform .2s ease-out}
.tarjeta:after{content:"";position:absolute;inset:0;pointer-events:none;z-index:5;
 background:linear-gradient(115deg,transparent 40%,rgba(255,243,210,.55) 50%,transparent 60%);
 transform:translateX(-130%);animation:brillo 5s ease-in-out 2.2s infinite}
@keyframes brillo{0%{transform:translateX(-130%)}35%,100%{transform:translateX(130%)}}
.esq{position:absolute;width:92px;height:92px;pointer-events:none;z-index:3;opacity:.95}
.esq.bl{bottom:6px;left:6px}
.esq.br{bottom:6px;right:6px;transform:scaleX(-1)}
.esq.tl{top:6px;left:6px;transform:scaleY(-1)}
.esq.tr{top:6px;right:6px;transform:scale(-1,-1)}
.foto{position:relative;height:250px;overflow:hidden}
.foto img{display:block;width:100%;height:100%;object-fit:cover;object-position:50% 28%;animation:zoom 16s ease-in-out infinite alternate}
@keyframes zoom{from{transform:scale(1)}to{transform:scale(1.08)}}
.foto:after{content:"";position:absolute;left:0;right:0;bottom:0;height:110px;background:linear-gradient(to bottom,rgba(255,253,249,0),#fffdf9)}
.cuerpo{position:relative;z-index:2;padding:30px 22px 34px;text-align:center}
.foto + .cuerpo{margin-top:-26px;padding-top:0}
.a{opacity:0;transform:translateY(16px)}
.inv.on .a{animation:sube .9s ease forwards;animation-delay:calc(var(--i) * .18s + .8s)}
@keyframes sube{to{opacity:1;transform:none}}
.t-inv{font-size:20px;font-style:italic;color:#7a6a58}
.nombre{font-size:46px;font-weight:700;line-height:1.08;color:#3b1520;margin:6px 0 2px;letter-spacing:.3px}
.orn{color:#b08d57;font-size:15px;letter-spacing:12px;margin:12px 0 4px}
.novios{font-family:'Pinyon Script',cursive;font-size:60px;line-height:1.15;color:#9c7a3f;margin:0}
.titulo{font-size:28px;font-weight:600;color:#3b1520;margin:4px 0 0}
.sub{font-size:19px;font-style:italic;color:#6d5d4c;margin:4px 0 0}
.fecha{display:inline-block;margin-top:18px;padding:9px 22px;border-top:1px solid #c7a76b;border-bottom:1px solid #c7a76b;
 font-size:22px;font-weight:600;color:#6e2433}
.desliza{margin-top:18px;font-size:17px;font-style:italic;color:#8a6d2b}
.desliza span{display:block;font-size:22px;animation:rebota 1.6s ease-in-out infinite}
@keyframes rebota{0%,100%{transform:translateY(0)}50%{transform:translateY(6px)}}
.petalos{position:absolute;inset:0;pointer-events:none;overflow:hidden;z-index:6}
.petalos i{position:absolute;top:-24px;border-radius:70% 0 70% 0;opacity:0;animation:caer linear infinite}
@keyframes caer{0%{transform:translate(0,-24px) rotate(0);opacity:0}10%{opacity:.85}100%{transform:translate(var(--dx),var(--h)) rotate(560deg);opacity:0}}

@media (max-width:480px){.foto{height:210px}.nombre{font-size:38px}.novios{font-size:52px}.tit b{font-size:40px}}
@media (prefers-reduced-motion:reduce){
 *{animation:none!important;transition:none!important}
 .a,.tarjeta{opacity:1!important;transform:none!important}
}
</style>

<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="rama" viewBox="0 0 100 100"><g fill="none" stroke="#b08d57" stroke-width="1.3" stroke-linecap="round">
<path d="M3 97 C 20 64, 46 36, 94 6"/>
<g fill="#e8d9b5" stroke-width=".9">
<ellipse cx="16" cy="74" rx="10" ry="4.2" transform="rotate(-70 16 74)"/>
<ellipse cx="25" cy="62" rx="10" ry="4.2" transform="rotate(-8 25 62)"/>
<ellipse cx="38" cy="50" rx="10" ry="4.2" transform="rotate(-80 38 50)"/>
<ellipse cx="49" cy="40" rx="10" ry="4.2" transform="rotate(-5 49 40)"/>
<ellipse cx="64" cy="29" rx="9" ry="3.8" transform="rotate(-75 64 29)"/>
<ellipse cx="76" cy="19" rx="9" ry="3.8" transform="rotate(-8 76 19)"/>
</g><circle cx="90" cy="9" r="2.2" fill="#c9a24b"/></g></symbol>
</defs></svg>

<div class="stage" id="stage">
  <div class="tit" id="tit"><small>Tienes una invitación</small><b>muy especial</b></div>
  <div class="escena" id="escena"><div class="bob">
    <div class="env" id="env">
      <div class="back"></div>
      <div class="flap"><div class="o"></div><div class="i"></div></div>
      <div class="mini"><div class="m1">Estás invitado a la boda de</div><div class="m2">__NOVIOS__</div><div class="m3">✦ ✦ ✦</div></div>
      <div class="bolsillo"><i class="l"></i><i class="r"></i><i class="b"></i></div>
      <div class="para"><small>Para</small><b id="pn">__NOMBRE__</b></div>
      <button class="seal" id="seal" aria-label="Abrir la invitación">__INI__</button>
    </div>
  </div></div>
  <div class="hint" id="hint">Toca el sello para abrir</div>
</div>

<div class="inv" id="inv">
  <div class="tarjeta" id="tarj">
    __ESQ_TOP__
    <svg class="esq bl" viewBox="0 0 100 100"><use href="#rama"/></svg>
    <svg class="esq br" viewBox="0 0 100 100"><use href="#rama"/></svg>
    __FOTO__
    <div class="cuerpo">
      <div class="a t-inv" style="--i:0">Con mucho cariño invitamos a</div>
      <div class="a nombre" style="--i:1">__NOMBRE__</div>
      <div class="a orn" style="--i:2">✦ ✦ ✦</div>
      <div class="a novios" style="--i:3">__NOVIOS__</div>
      <div class="a titulo" style="--i:4">__TITULO__</div>
      <div class="a sub" style="--i:5">__SUBTITULO__</div>
      <div class="a fecha" style="--i:6">__FECHA__</div>
      <div class="a desliza" style="--i:7">Desliza para ver todos los detalles<span>⌄</span></div>
    </div>
  </div>
  <div class="petalos" id="petalos"></div>
</div>

<script>
const $=id=>document.getElementById(id);
const env=$('env'),stage=$('stage'),inv=$('inv'),tarj=$('tarj');
const reducir=matchMedia('(prefers-reduced-motion:reduce)').matches;
let abierto=false;
const AUTO=__AUTO__,VEL=__VEL__;

function escala(){const k=Math.min(1,(innerWidth-24)/340);$('escena').style.transform='scale('+k+')'}
escala();addEventListener('resize',escala);

function fit(){try{window.frameElement.style.height=(Math.ceil(inv.getBoundingClientRect().height)+8)+'px'}catch(e){}}
new ResizeObserver(()=>{if(abierto)fit()}).observe(inv);

/* ajusta el tamaño del nombre en el sobre si es muy largo */
(function(){const n=$('pn'),L=n.textContent.length;if(L>24)n.style.fontSize='19px';else if(L>16)n.style.fontSize='24px'})();

/* destellos dorados alrededor del sobre */
for(let i=0;i<16;i++){const s=document.createElement('b');s.className='sp';
  s.style.cssText='left:'+(8+Math.random()*84)+'%;top:'+(12+Math.random()*76)+'%;animation-delay:'+(-Math.random()*3.4)+'s;animation-duration:'+(2.6+Math.random()*2.4)+'s';
  stage.appendChild(s)}

function chispas(){
  for(let i=0;i<18;i++){
    const p=document.createElement('i');p.className='ch';env.appendChild(p);
    const a=Math.random()*Math.PI*2,d=60+Math.random()*90;
    p.animate([{transform:'translate(0,0) scale(1)',opacity:1},
               {transform:'translate('+Math.cos(a)*d+'px,'+(Math.sin(a)*d-20)+'px) scale(.2)',opacity:0}],
              {duration:900+Math.random()*400,easing:'cubic-bezier(.15,.8,.3,1)'}).onfinish=()=>p.remove();
  }
}

function petalos(){
  const c=$('petalos'),cols=['#e8d3b0','#f0e0c4','#d9b48a','#c9a24b','#ead0c6'],h=inv.getBoundingClientRect().height+30;
  for(let i=0;i<18;i++){
    const p=document.createElement('i'),s=8+Math.random()*10;
    p.style.cssText='left:'+(Math.random()*100)+'%;width:'+s+'px;height:'+(s*1.3)+'px;background:'+cols[i%cols.length]+
      ';animation-duration:'+(8+Math.random()*7)+'s;animation-delay:'+(Math.random()*6)+'s;--dx:'+(Math.random()*90-45)+'px;--h:'+h+'px';
    c.appendChild(p);
  }
}

function autoScroll(){
  let P,D;try{P=window.parent;D=P.document;D.body}catch(e){return}
  if(reducir)return;
  try{P.__autoOff&&P.__autoOff()}catch(e){}
  let el=null;
  for(const q of ['[data-testid="stMain"]','section.main','[data-testid="stAppViewContainer"]']){
    const x=D.querySelector(q);if(x&&x.scrollHeight>x.clientHeight+50){el=x;break}}
  if(!el)el=D.scrollingElement||D.documentElement;
  let pos=el.scrollTop,ult=pos,t0=null,raf=0,corre=false,estado='';
  const btn=D.createElement('button');
  btn.setAttribute('aria-label','Pausar o seguir el recorrido automático');
  btn.style.cssText='position:fixed;right:16px;bottom:16px;z-index:999999;padding:9px 16px;border-radius:999px;border:1px solid #c7a76b;background:rgba(255,253,249,.95);color:#6e2433;font:600 17px "Cormorant Garamond",Georgia,serif;cursor:pointer;box-shadow:0 6px 18px rgba(70,40,30,.25)';
  D.body.appendChild(btn);
  const pinta=()=>{btn.textContent=corre?'⏸ Pausar':(estado==='fin'?'↺ Ver de nuevo':'▶ Seguir')};
  const ir=y=>{try{el.scrollTo({top:y,behavior:'instant'})}catch(e){el.scrollTop=y}};
  function paso(ts){
    if(!corre)return;
    if(t0===null)t0=ts;
    const dt=Math.min(ts-t0,100);t0=ts;
    if(Math.abs(el.scrollTop-ult)>4){parar();return}      /* el invitado movió la página */
    const max=el.scrollHeight-el.clientHeight;
    pos+=VEL*dt/1000;
    if(pos>=max-1){ir(max);estado='fin';parar();return}
    ir(pos);ult=el.scrollTop;
    raf=P.requestAnimationFrame(paso);
  }
  function seguir(){if(corre)return;estado='';pos=el.scrollTop;ult=pos;t0=null;corre=true;pinta();raf=P.requestAnimationFrame(paso)}
  function parar(){corre=false;P.cancelAnimationFrame(raf);pinta()}
  const manual=e=>{if(e.target===btn)return;if(corre)parar()};
  const evs=['wheel','touchstart','mousedown','keydown'];
  evs.forEach(n=>D.addEventListener(n,manual,{passive:true,capture:true}));
  btn.onclick=()=>{
    if(corre)parar();
    else if(estado==='fin'){estado='';ir(0);setTimeout(seguir,700)}
    else seguir();
  };
  const off=()=>{corre=false;try{P.cancelAnimationFrame(raf)}catch(e){}
    evs.forEach(n=>D.removeEventListener(n,manual,{capture:true}));btn.remove()};
  P.__autoOff=off;
  addEventListener('pagehide',off);
  seguir();
}

function mostrar(){
  stage.classList.add('fuera');
  stage.style.cssText+=';position:absolute;left:0;right:0;top:0';
  inv.classList.add('on');
  fit();petalos();
  setTimeout(()=>{stage.style.display='none';fit()},950);
  setTimeout(()=>tarj.classList.add('listo'),1500);
  if(AUTO)setTimeout(autoScroll,4500);
}

function abrir(){
  if(abierto)return;abierto=true;
  try{const a=window.parent.document.querySelector('audio');if(a){a.volume=.7;const r=a.play();if(r&&r.catch)r.catch(()=>{})}}catch(e){}
  if(reducir){mostrar();return}
  chispas();
  env.classList.add('rompe');
  $('tit').style.opacity=0;$('hint').style.opacity=0;
  setTimeout(()=>env.classList.add('abre'),380);
  setTimeout(()=>env.classList.add('atras'),850);
  setTimeout(()=>env.classList.add('sale'),1450);
  setTimeout(()=>env.classList.add('frente'),2650);
  setTimeout(mostrar,3500);
}
$('seal').addEventListener('click',e=>{e.stopPropagation();abrir()});
env.addEventListener('click',abrir);

/* pequeña inclinación 3D de la tarjeta con el mouse */
tarj.addEventListener('pointermove',e=>{
  if(!tarj.classList.contains('listo')||e.pointerType==='touch')return;
  const r=tarj.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
  tarj.style.transform='perspective(1000px) rotateY('+(x*6)+'deg) rotateX('+(-y*5)+'deg)';
});
tarj.addEventListener('pointerleave',()=>{tarj.style.transform=''});
</script>
"""


def iniciales_novios():
    partes = [p.strip() for p in NOVIOS.split("&") if p.strip()]
    return " & ".join(p[0].upper() for p in partes) if partes else NOVIOS[:1]


def bloque_sobre(nombre):
    """Sobre beige que se abre y deja ver la invitación."""
    portada = foto_uri(FOTO_PORTADA)
    foto = (f'<div class="foto"><img src="{portada}" alt="{html.escape(NOVIOS)}"></div>' if portada else "")
    esq_top = "" if portada else ('<svg class="esq tl" viewBox="0 0 100 100"><use href="#rama"/></svg>'
                                  '<svg class="esq tr" viewBox="0 0 100 100"><use href="#rama"/></svg>')
    page = (SOBRE_HTML
            .replace("__ALTO__", str(ALTO_SOBRE))
            .replace("__AUTO__", "true" if AUTOSCROLL else "false")
            .replace("__VEL__", str(float(VELOCIDAD_AUTO)))
            .replace("__FOTO__", foto)
            .replace("__ESQ_TOP__", esq_top)
            .replace("__INI__", html.escape(iniciales_novios()))
            .replace("__NOVIOS__", html.escape(NOVIOS))
            .replace("__NOMBRE__", html.escape(nombre))
            .replace("__TITULO__", html.escape(TITULO_EVENTO))
            .replace("__SUBTITULO__", html.escape(SUBTITULO))
            .replace("__FECHA__", html.escape(FECHA_TEXTO)))
    components.html(page, height=ALTO_SOBRE)


def vista_invitado(codigo):
    with con() as c:
        g = c.execute("SELECT * FROM invitados WHERE codigo=?", (codigo,)).fetchone()
    if not g:
        st.error("Este enlace no es válido. Pídele uno nuevo a quien te invitó.")
        return

    bloque_sobre(g["nombre"])

    if MUSICA and os.path.exists(MUSICA):
        st.caption("🎵 La música suena al abrir el sobre; si no se oye, dale play aquí")
        st.audio(MUSICA)

    st.markdown('<div class="sec">Falta muy poco</div>', unsafe_allow_html=True)
    bloque_cuenta_y_calendario()

    st.markdown('<div class="sec">Itinerario</div>', unsafe_allow_html=True)
    st.markdown(itinerario_html(), unsafe_allow_html=True)

    st.markdown('<div class="sec">Nuestra historia</div>', unsafe_allow_html=True)
    if FRASE:
        st.markdown(f'<div class="frase"><span class="cm">“</span>{html.escape(FRASE)}<span class="cm">”</span></div>',
                    unsafe_allow_html=True)
    bloque_galeria()

    st.markdown('<div class="sec">Dónde nos vemos</div>', unsafe_allow_html=True)
    extras = f'<div class="l" style="margin-top:6px">{html.escape(EXTRAS)}</div>' if EXTRAS else ""
    st.markdown(
        '<div class="lugar"><div class="t">⛪ Ceremonia religiosa</div>'
        f'<div class="h">{html.escape(MISA_HORA)}</div><div class="l">{html.escape(MISA_LUGAR)}</div></div>'
        '<div class="lugar"><div class="t">🥂 Celebración</div>'
        f'<div class="h">{html.escape(FIESTA_HORA)}</div><div class="l">{html.escape(FIESTA_LUGAR)}</div>{extras}</div>',
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns(3)
    b1.link_button("⛪ Cómo llegar a la misa", (MISA_MAPA_URL or maps(MISA_MAPA)), use_container_width=True)
    b2.link_button("🥂 Cómo llegar a la fiesta", (FIESTA_MAPA_URL or maps(FIESTA_MAPA)), use_container_width=True)
    b3.download_button("📆 Guardar en mi calendario", archivo_calendario(), "boda.ics",
                       "text/calendar", use_container_width=True)

    vest = (f'<div class="nota" style="padding:10px">👗 Vestimenta: <b>{html.escape(VESTIMENTA)}</b></div>'
            if VESTIMENTA else "")
    contacto = ""
    if CONTACTOS:
        links = " · ".join(f'<a href="https://wa.me/57{n}" target="_blank" style="color:#6e2433">{n}</a>'
                           for n in CONTACTOS)
        contacto = f'<div class="nota" style="padding:10px;font-size:18px">📞 ¿Dudas? Escríbenos: {links}</div>'
    st.markdown(
        f'{vest}'
        f'<div class="nota msg">{html.escape(MENSAJE)}</div>{contacto}',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sec">Confirma tu asistencia</div>', unsafe_allow_html=True)
    if g["estado"] == "Confirmado":
        st.success("Ya confirmaste tu asistencia. ¡Te esperamos! Puedes cambiar tu respuesta aquí abajo.")
    elif g["estado"] == "No asiste":
        st.info("Registramos que no podrás asistir. Si cambias de opinión, actualiza tu respuesta.")

    idx = {"Confirmado": 0, "No asiste": 1}.get(g["estado"])
    with st.form("rsvp"):
        opcion = st.radio("¿Nos acompañas?", ["¡Sí, ahí estaré! 🎊", "No podré asistir 😢"], index=idx)
        extra = st.number_input("¿Cuántos acompañantes llevas? (sin contarte)", 0, 10, int(g["acompanantes"]))
        msg = st.text_area("Déjanos un mensaje para los novios (opcional)", value=g["mensaje"] or "", max_chars=300)
        enviar = st.form_submit_button("Enviar respuesta")

    if enviar:
        if opcion is None:
            st.warning("Elige una opción primero.")
            return
        vienen = opcion.startswith("¡Sí")
        with con() as c:
            c.execute(
                "UPDATE invitados SET estado=?, acompanantes=?, mensaje=?, fecha_respuesta=? WHERE codigo=?",
                ("Confirmado" if vienen else "No asiste", int(extra) if vienen else 0,
                 msg.strip(), datetime.now().strftime("%Y-%m-%d %H:%M"), codigo),
            )
        if vienen:
            st.balloons()
            st.success("¡Gracias por confirmar! Nos vemos pronto 💜")
            st.markdown(
                '<div class="pase"><div class="top">Pase de entrada · Boda</div>'
                f'<div class="cuerpo"><div class="n">{html.escape(g["nombre"])}</div>'
                f'<div>{html.escape(NOVIOS)}</div>'
                f'<div style="margin-top:6px">{html.escape(FECHA_TEXTO)}</div></div>'
                '<div class="corte"></div>'
                f'<div class="abajo">🎟️ Personas confirmadas: <b>{1 + int(extra)}</b><br>'
                f'⛪ {html.escape(MISA_HORA)} · 🥂 {html.escape(FIESTA_HORA)}<br>'
                '<i>Tómale captura de pantalla a este pase 📸</i></div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Gracias por avisarnos. ¡Te vamos a extrañar!")



def telefono_wa(t):
    t = "".join(ch for ch in (t or "") if ch.isdigit())
    if len(t) == 10:      # celular colombiano sin indicativo
        t = "57" + t
    return t


def enlace_publico():
    """Lee el enlace público que crea iniciar.bat (cloudflared) en tunel.log. Devuelve (enlace, existe_log)."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tunel.log")
    if not os.path.exists(ruta):
        return None, False
    try:
        with open(ruta, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
    except OSError:
        return None, True
    urls = [u for u in re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", txt) if not u.startswith("https://api.")]
    return (urls[-1] if urls else None), True


def vista_admin():
    st.title("Panel de los novios 💍")
    if st.text_input("Clave", type="password") != CLAVE_ADMIN:
        st.info("Escribe la clave para continuar.")
        return

    try:
        host = st.context.headers.get("Host", "")
    except Exception:
        host = ""
    sugerida = ("http://" if host.startswith(("localhost", "127.")) else "https://") + host if host else "http://localhost:8501"
    publico, hay_log = enlace_publico()
    if publico:
        sugerida = publico
        st.success(f"🌐 Enlace público activo: {publico}  — los enlaces de abajo ya sirven para enviar a tus invitados.")
    elif hay_log:
        st.warning("Todavía no aparece el enlace público (tarda unos segundos en crearse).")
        st.button("🔄 Buscar enlace público")
    base = st.text_input("Dirección pública de tu app (para armar los enlaces)", sugerida)

    st.subheader("Agregar invitados")
    st.caption("Uno por línea. Si quieres, añade el celular al final separado por coma. "
               "Ej: Familia Pérez, 3101234567")
    nombres = st.text_area("Invitados")
    if st.button("Agregar"):
        with con() as c:
            for linea in [x.strip() for x in nombres.splitlines() if x.strip()]:
                nombre, tel = linea, ""
                if "," in linea:
                    ini, fin = linea.rsplit(",", 1)
                    solo = "".join(ch for ch in fin if ch.isdigit())
                    if len(solo) >= 7:
                        nombre, tel = ini.strip(), solo
                c.execute("INSERT INTO invitados(codigo, nombre, telefono) VALUES(?,?,?)",
                          (secrets.token_urlsafe(5), nombre, tel))
        st.rerun()

    with con() as c:
        df = pd.read_sql_query("SELECT * FROM invitados ORDER BY nombre", c)
    if df.empty:
        st.info("Aún no hay invitados.")
        return

    df["enlace"] = base.rstrip("/") + "/?c=" + df["codigo"]
    conf = df[df["estado"] == "Confirmado"]
    a, b, c3, d = st.columns(4)
    a.metric("Invitados", len(df))
    b.metric("Confirmaron", len(conf))
    c3.metric("No asisten", int((df["estado"] == "No asiste").sum()))
    d.metric("Personas en total", int(len(conf) + conf["acompanantes"].sum()))

    cols = {"nombre": "Invitado", "telefono": "Celular", "estado": "Estado", "acompanantes": "Acompañantes",
            "mensaje": "Mensaje", "fecha_respuesta": "Fecha respuesta", "enlace": "Enlace"}
    vista = df[list(cols)].rename(columns=cols)
    st.dataframe(vista, use_container_width=True, hide_index=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        vista[vista["Estado"] == "Confirmado"].to_excel(w, sheet_name="Confirmados", index=False)
        vista.to_excel(w, sheet_name="Todos", index=False)
    st.download_button("📥 Descargar lista en Excel", buf.getvalue(), "invitados.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.subheader("📲 Enviar invitaciones por WhatsApp")
    st.caption("Primero pega arriba tu dirección pública (https://...). Luego toca el botón de cada invitado: "
               "se abre WhatsApp con el mensaje y su enlace listos para enviar.")
    for _, r in df.iterrows():
        texto = (f"¡Hola {r['nombre']}! 💍 Steven y Emely te invitamos a nuestra boda. "
                 f"Abre tu invitación personal y confirma tu asistencia aquí: {r['enlace']}")
        tel = telefono_wa(r["telefono"])
        url = (f"https://wa.me/{tel}?text=" if tel else "https://wa.me/?text=") + quote(texto)
        x1, x2 = st.columns([3, 2])
        x1.write(f"**{r['nombre']}** · {r['estado']}")
        x2.link_button("Enviar por WhatsApp", url, use_container_width=True)

    with st.expander("Eliminar un invitado"):
        quien = st.selectbox("Invitado", df["nombre"])
        if st.button("Eliminar"):
            with con() as c:
                c.execute("DELETE FROM invitados WHERE nombre=?", (quien,))
            st.rerun()


st.set_page_config(page_title="Boda " + NOVIOS, page_icon=EMOJI, layout="centered")
st.markdown(ESTILO, unsafe_allow_html=True)
iniciar()

codigo = st.query_params.get("c")
if codigo:
    vista_invitado(codigo)
elif st.query_params.get("admin") == "1":
    vista_admin()
else:
    st.info("Abre el enlace personal de tu invitación.")
    if st.button("Soy uno de los novios 💍"):
        st.query_params["admin"] = "1"
        st.rerun()
