# Genera /tt y /tt/agendar (carril TikTok) a partir de la landing de Meta SIN tocar los originales.
# Uso: python scripts/generar-tt.py   (regenerar cada vez que cambie index.html o agendar/index.html)
# Cada reemplazo exige encontrar el patrón exactamente las veces esperadas (si la landing
# cambia, el script falla en vez de producir una copia a medias).
import pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[1]


def read(p):
    return (REPO / p).read_bytes().decode("utf-8").replace("\r\n", "\n")


def sub1(s, old, new, count=1, regex=False):
    n = len(re.findall(old, s, re.S)) if regex else s.count(old)
    if n != count:
        sys.exit(f"patrón encontrado {n} veces (esperaba {count}): {old[:90]!r}")
    return re.sub(old, lambda _m: new, s, flags=re.S) if regex else s.replace(old, new)


META_PIXEL = re.compile(r"<!-- Meta Pixel Code -->.*?<!-- End Meta Pixel Code -->\n", re.S)

# Código base oficial de TikTok (ttq) SIN ttq.load/ttq.page: solo define la cola.
# El load + PageView lo entrega /tt/pixel.js (función de Netlify) con el ID de la variable
# de entorno NEXT_PUBLIC_TIKTOK_PIXEL_ID; si la variable no existe, /tt/pixel.js viene vacío
# y aquí no se carga nada ni truena nada (los ttq.track quedan en una cola que nadie lee).
TIKTOK_HEAD = """<!-- TikTok Pixel Code (carril TikTok: SOLO /tt) -->
<script>
!function (w, d, t) {
  w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie","holdConsent","revokeConsent","grantConsent"],ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){for(
var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e},ttq.load=function(e,n){var r="https://analytics.tiktok.com/i18n/pixel/events.js",o=n&&n.partner;ttq._i=ttq._i||{},ttq._i[e]=[],ttq._i[e]._u=r,ttq._t=ttq._t||{},ttq._t[e]=+new Date,ttq._o=ttq._o||{},ttq._o[e]=n||{};n=document.createElement("script")
;n.type="text/javascript",n.async=!0,n.src=r+"?sdkid="+e+"&lib="+t;e=document.getElementsByTagName("script")[0];e.parentNode.insertBefore(n,e)};
}(window, document, 'ttq');
</script>
<script async src="/tt/pixel.js"></script>
<!-- End TikTok Pixel Code -->
"""

# Atribución del carril: utm_source/utm_campaign/utm_content/ttclid de la URL del anuncio,
# con respaldo en sessionStorage (el lead puede navegar antes de agendar).
TT_ATTR_JS = """var TT_KEYS=['utm_source','utm_campaign','utm_content','ttclid'];
function ttAttr(){var o={};try{var q=new URLSearchParams(location.search);TT_KEYS.forEach(function(k){var v=q.get(k)||'';if(!v){try{v=sessionStorage.getItem('tt_'+k)||''}catch(e){}}if(v)o[k]=String(v).slice(0,200);});}catch(e){}return o;}
function ttAgendarUrl(){var u=new URL('/tt/agendar',location.origin);var a=ttAttr();Object.keys(a).forEach(function(k){u.searchParams.set(k,a[k]);});return u.pathname+u.search;}
function ttClick(etiqueta){try{if(window.ttq&&typeof window.ttq.track==='function')window.ttq.track('ClickButton',{content_name:etiqueta});}catch(e){}}"""


def build_index():
    s = read("index.html")
    s = sub1(s, META_PIXEL.pattern, "", regex=True)
    # Google Ads fuera de /tt: sus conversiones contarían clics de TikTok como de Google.
    s = sub1(s, r"<!-- Google tag \(gtag\.js\) -->\n", "", count=len(re.findall(r"<!-- Google tag \(gtag\.js\) -->\n", s)), regex=True)
    s = sub1(s, r"<script async src=\"https://www\.googletagmanager\.com/gtag/js\?id=AW-18326006064\"></script>\n<script>\nwindow\.dataLayer.*?</script>\n", "", regex=True)
    s = sub1(s, '<meta name="facebook-domain-verification" content="9e74jisnzitw7xk20s2rdyyx2jqno0" />\n', "")
    s = sub1(s, '<meta charset="UTF-8">\n', '<meta charset="UTF-8">\n<meta name="robots" content="noindex">\n' + TIKTOK_HEAD)
    # Botones de agendar -> /tt/agendar (funcionan aunque falle el JS)
    s = sub1(s, 'href="/agendar?utm_source=mev&amp;utm_content=cursos-ingreso"', 'href="/tt/agendar"')
    s = sub1(s, 'href="/agendar"', 'href="/tt/agendar"', count=2)
    # Handlers de clic: ClickButton de TikTok en lugar de fbq/gtag
    old_handlers = re.search(r"<script>\nfunction trackCal\(e\) \{.*?</script>\n", s, re.S)
    if not old_handlers:
        sys.exit("no encontré el bloque trackCal")
    new_handlers = ("<script>\n" + TT_ATTR_JS + "\n"
                    "function trackCal(e){e.preventDefault();ttClick('agendar_videollamada');var d=ttAgendarUrl();setTimeout(function(){window.location.href=d;},300);}\n"
                    "function trackCalCursos(e){e.preventDefault();ttClick('agendar_videollamada_cursos_ingreso');var d=ttAgendarUrl();setTimeout(function(){window.location.href=d;},300);}\n"
                    "/* Clics al ecosistema: en /tt no se mide con pixeles de Meta ni de Google */\n"
                    "function trackCrossSell(destino){}\n"
                    "</script>\n")
    s = s.replace(old_handlers.group(0), new_handlers)
    # Scroll50/Scroll75 eran eventos de Meta: fuera
    s = sub1(s, r"<script>\n\(function\(\)\{\n  function fired\(k\).*?</script>\n", "", regex=True)
    # Atribución: la de Meta (anuncio/conjunto -> /agendar) se cambia por la de TikTok
    s = sub1(s, r"<!-- MEV atribución: anuncio/conjunto.*?</script>\n", (
        "<!-- Carril TikTok: utm_source/utm_campaign/utm_content/ttclid viajan de la URL del anuncio a /tt/agendar -->\n"
        "<script>\n(function(){try{\n  var q=new URLSearchParams(location.search);\n"
        "  ['utm_source','utm_campaign','utm_content','ttclid'].forEach(function(k){var v=q.get(k);if(v){try{sessionStorage.setItem('tt_'+k,String(v).slice(0,200))}catch(e){}}});\n"
        "  var d=ttAgendarUrl();\n"
        "  document.querySelectorAll('a[href^=\"/tt/agendar\"]').forEach(function(l){l.setAttribute('href',d);});\n"
        "}catch(e){}})();\n</script>\n"), regex=True, count=1)
    for bad in ("fbq", "facebook", "gtag", "googletagmanager", "2131352721031916", "AW-18326006064", "\"/agendar", "'/agendar"):
        if bad in s:
            sys.exit(f"quedó '{bad}' en tt/index.html")
    return s


def build_agendar():
    s = read("agendar/index.html")
    s = sub1(s, META_PIXEL.pattern, "", regex=True)
    s = sub1(s, '<meta charset="UTF-8">\n', '<meta charset="UTF-8">\n<meta name="robots" content="noindex">\n' + TIKTOK_HEAD)
    s = sub1(s, '<a class="nav-logo" href="/">', '<a class="nav-logo" href="/tt">')
    s = sub1(s, "https://cal.com/team/mev-sales-team/mevi-informes", "https://cal.com/team/mev-sales-team/mev-informes-tt")
    s = sub1(s, 'Cal("init", "mevi-informes", {origin:"https://app.cal.com"});', 'Cal("init", "mev-informes-tt", {origin:"https://app.cal.com"});')
    # metadata anuncio/conjunto (Meta) -> metadata utm_*/ttclid (TikTok)
    s = sub1(s, r"  /\* MEV atribuci.*?  \} catch \(e\) \{\}\n", (
        "  /* Carril TikTok: utm_source/utm_campaign/utm_content/ttclid llegan en la URL (desde /tt)\n"
        "     o en sessionStorage y viajan a cal.com como metadata de la reserva -> webhook\n"
        "     mev-tt-videollamada -> columnas utm_* / ttclid del Sheet MEV - Videollamadas. */\n"
        "  var __mevCfg = {\"layout\":\"month_view\",\"theme\":\"dark\"};\n"
        "  try {\n"
        "    var __q = new URLSearchParams(location.search);\n"
        "    [\"utm_source\",\"utm_campaign\",\"utm_content\",\"ttclid\"].forEach(function (k) {\n"
        "      var v = __q.get(k) || \"\";\n"
        "      if (v) { try { sessionStorage.setItem(\"tt_\" + k, String(v).slice(0, 200)); } catch (e) {} }\n"
        "      else { try { v = sessionStorage.getItem(\"tt_\" + k) || \"\"; } catch (e) {} }\n"
        "      if (v) __mevCfg[\"metadata[\" + k + \"]\"] = String(v).slice(0, 200);\n"
        "    });\n"
        "  } catch (e) {}\n"), regex=True)
    s = sub1(s, 'Cal.ns["mevi-informes"]("inline", {', 'Cal.ns["mev-informes-tt"]("inline", {')
    s = sub1(s, 'calLink: "team/mev-sales-team/mevi-informes",', 'calLink: "team/mev-sales-team/mev-informes-tt",')
    s = sub1(s, 'Cal.ns["mevi-informes"]("ui", {', 'Cal.ns["mev-informes-tt"]("ui", {')
    # Sin Schedule de Meta al reservar: se quita el callback bookingSuccessful completo
    s = sub1(s, r"  /\* Al completarse la reserva dentro del embed.*?Cal\.ns\[\"mevi-informes\"\]\(\"on\", \{\n    action: \"bookingSuccessful\",\n    callback: window\.__mevOnBooking\n  \}\);\n\n", "", regex=True)
    s = sub1(s, 'Cal.ns["mevi-informes"]("on", {\n    action: "linkReady",', 'Cal.ns["mev-informes-tt"]("on", {\n    action: "linkReady",')
    s = sub1(s, "my-cal-inline-mevi-informes", "my-cal-inline-mev-informes-tt", count=3)
    for bad in ("fbq", "facebook", "2131352721031916", "mevi-informes\"", "__mevOnBooking", "Schedule"):
        if bad in s:
            sys.exit(f"quedó '{bad}' en tt/agendar/index.html")
    return s


if __name__ == "__main__":
    idx, ag = build_index(), build_agendar()
    (REPO / "tt" / "agendar").mkdir(parents=True, exist_ok=True)
    (REPO / "tt" / "index.html").write_bytes(idx.encode("utf-8"))
    (REPO / "tt" / "agendar" / "index.html").write_bytes(ag.encode("utf-8"))
    print("OK tt/index.html", len(idx), "| tt/agendar/index.html", len(ag))
