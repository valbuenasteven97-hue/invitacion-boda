import streamlit as st
import streamlit.components.v1 as components
import sqlite3, secrets, io, html, os, base64, calendar
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

SOBRES = ("Tu presencia es nuestro mejor regalo. Si deseas tener un detalle con nosotros, "
          "habrá una hermosa lluvia de sobres 💌")
MENSAJE = "Gracias por ser parte de nuestra historia. ¡Te esperamos!"
VESTIMENTA = "Libre"   # déjalo vacío ("") para no mostrarlo
EXTRAS = "🍖 Asado · 🎺 Orquesta · 🎧 DJ"   # lo que habrá en la fiesta; vacío ("") para ocultar
CONTACTOS = ["3214569187", "3213059268"]   # para dudas
FRASE = ""   # aquí irá la frase de ustedes (la dejamos para después); vacío para ocultar
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
DB = "invitacion.db"
# ===================================================

ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Pinyon+Script&display=swap');
.stApp{background:#f6f0e6;}
.stApp, .stApp p, .stApp label{font-family:'Cormorant Garamond',Georgia,serif;}
.hero{max-width:600px;margin:14px auto 22px;background:#fffdf9;border:1px solid #c7a76b;
outline:1px solid #e3d2ac;outline-offset:6px;overflow:hidden;box-shadow:0 22px 50px rgba(70,40,30,.18);
font-family:'Cormorant Garamond',Georgia,serif;color:#2b2523;animation:entra 1.2s ease both}
@keyframes entra{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.hero .foto{position:relative}
.hero .foto img{display:block;width:100%;height:420px;object-fit:cover;object-position:50% 28%}
.hero .foto:after{content:"";position:absolute;left:0;right:0;bottom:0;height:140px;
background:linear-gradient(to bottom,rgba(255,253,249,0),#fffdf9)}
.hero .cuerpo{padding:0 24px 36px;text-align:center;margin-top:-30px;position:relative;z-index:2}
.hero .inv{font-size:20px;font-style:italic;color:#7a6a58}
.hero .nombre{font-size:46px;font-weight:700;line-height:1.08;color:#3b1520;margin:6px 0 2px;letter-spacing:.3px}
.hero .orn{color:#b08d57;font-size:15px;letter-spacing:12px;margin:14px 0 6px}
.hero .novios{font-family:'Pinyon Script',cursive;font-size:60px;line-height:1.15;color:#9c7a3f;margin:0}
.hero .titulo{font-size:28px;font-weight:600;color:#3b1520;margin:6px 0 0}
.hero .sub{font-size:19px;font-style:italic;color:#6d5d4c;margin:4px 0 0}
.hero .fecha{display:inline-block;margin-top:20px;padding:9px 22px;border-top:1px solid #c7a76b;
border-bottom:1px solid #c7a76b;font-size:22px;font-weight:600;color:#6e2433}
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
@media (prefers-reduced-motion:reduce){.hero{animation:none}}
@media (max-width:480px){.hero .foto img{height:340px}.hero .nombre{font-size:38px}.hero .novios{font-size:52px}}
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


def vista_invitado(codigo):
    with con() as c:
        g = c.execute("SELECT * FROM invitados WHERE codigo=?", (codigo,)).fetchone()
    if not g:
        st.error("Este enlace no es válido. Pídele uno nuevo a quien te invitó.")
        return

    portada = foto_uri(FOTO_PORTADA)
    img = f'<div class="foto"><img src="{portada}" alt="{html.escape(NOVIOS)}"></div>' if portada else ""
    st.markdown(
        '<div class="hero">' + img +
        '<div class="cuerpo">'
        '<div class="inv">Con mucho cariño invitamos a</div>'
        f'<div class="nombre">{html.escape(g["nombre"])}</div>'
        '<div class="orn">✦ ✦ ✦</div>'
        f'<p class="novios">{html.escape(NOVIOS)}</p>'
        f'<p class="titulo">{html.escape(TITULO_EVENTO)}</p>'
        f'<p class="sub">{html.escape(SUBTITULO)}</p>'
        f'<div class="fecha">{html.escape(FECHA_TEXTO)}</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    if MUSICA and os.path.exists(MUSICA):
        st.caption("🎵 Dale play para escuchar la música de nuestra boda")
        st.audio(MUSICA)

    st.markdown('<div class="sec">Falta muy poco</div>', unsafe_allow_html=True)
    bloque_cuenta_y_calendario()

    st.markdown('<div class="sec">Itinerario</div>', unsafe_allow_html=True)
    st.markdown(itinerario_html(), unsafe_allow_html=True)

    st.markdown('<div class="sec">Nuestra historia</div>', unsafe_allow_html=True)
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
    b1.link_button("⛪ Cómo llegar a la misa", maps(MISA_MAPA), use_container_width=True)
    b2.link_button("🥂 Cómo llegar a la fiesta", maps(FIESTA_MAPA), use_container_width=True)
    b3.download_button("📆 Guardar en mi calendario", archivo_calendario(), "boda.ics",
                       "text/calendar", use_container_width=True)

    vest = (f'<div class="nota" style="padding:10px">👗 Vestimenta: <b>{html.escape(VESTIMENTA)}</b></div>'
            if VESTIMENTA else "")
    frase = f'<div class="nota msg">“{html.escape(FRASE)}”</div>' if FRASE else ""
    contacto = ""
    if CONTACTOS:
        links = " · ".join(f'<a href="https://wa.me/57{n}" target="_blank" style="color:#6e2433">{n}</a>'
                           for n in CONTACTOS)
        contacto = f'<div class="nota" style="padding:10px;font-size:18px">📞 ¿Dudas? Escríbenos: {links}</div>'
    st.markdown(
        f'{vest}<div class="nota">{html.escape(SOBRES)}</div>{frase}'
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
