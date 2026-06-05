"""Planisphère 3D — carte bleu foncé stylisée + flux de transferts animés."""

from __future__ import annotations

import json
import time
from collections import defaultdict

import streamlit.components.v1 as components

GLOBE_VERSION = "v5-spin"

COUNTRY_COORDS: dict[str, tuple[float, float, str]] = {
    "FR": (46.2276, 2.2137, "France"),
    "JP": (36.2048, 138.2529, "Japon"),
    "US": (37.0902, -95.7129, "États-Unis"),
    "DE": (51.1657, 10.4515, "Allemagne"),
    "GB": (55.3781, -3.4360, "Royaume-Uni"),
    "ES": (40.4637, -3.7492, "Espagne"),
    "IT": (41.8719, 12.5674, "Italie"),
    "CN": (35.8617, 104.1954, "Chine"),
    "BR": (-14.2350, -51.9253, "Brésil"),
    "SN": (14.4974, -14.4524, "Sénégal"),
    "TG": (8.6195, 0.8248, "Togo"),
    "BJ": (9.3077, 2.3158, "Bénin"),
    "NG": (9.0820, 8.6753, "Nigéria"),
    "CA": (56.1304, -106.3468, "Canada"),
    "AU": (-25.2744, 133.7751, "Australie"),
    "IN": (20.5937, 78.9629, "Inde"),
    "MX": (23.6345, -102.5528, "Mexique"),
}

GEOJSON_URL = (
    "https://cdn.jsdelivr.net/gh/holtzy/D3-graph-gallery@master/DATA/world.geojson"
)


def _coords(code: str) -> tuple[float, float, str]:
    code = str(code).strip().upper()
    return COUNTRY_COORDS.get(code, (20.0, float((hash(code) % 360) - 180), code))


def _country_signals(df) -> list[dict]:
    if df is None or df.empty or "country" not in df.columns:
        return []

    signals = []
    for code, group in df.groupby("country", dropna=True):
        code = str(code).strip().upper()
        if not code:
            continue

        alerts = int(group["is_suspicious"].sum()) if "is_suspicious" in group.columns else 0
        max_score = float(group["fraud_score"].max()) if "fraud_score" in group.columns else 0.0
        lat, lon, name = _coords(code)

        signals.append({
            "code": code,
            "name": name,
            "lat": lat,
            "lon": lon,
            "alerts": alerts,
            "risk": "high" if alerts > 0 and max_score >= 0.7 else "medium" if alerts > 0 else "low",
        })

    return signals


def _transfer_flows(df) -> list[dict]:
    if df is None or df.empty or "country" not in df.columns:
        return []

    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"count": 0, "amount": 0.0, "suspicious": 0}
    )

    sort_cols = [c for c in ("timestamp", "transaction_id") if c in df.columns]
    work = df.dropna(subset=["country"]).copy()

    if "user_id" in work.columns:
        for _, group in work.groupby("user_id"):
            ordered = group.sort_values(sort_cols) if sort_cols else group
            rows = ordered.to_dict("records")
            for i in range(len(rows) - 1):
                src = str(rows[i].get("country", "")).strip().upper()
                dst = str(rows[i + 1].get("country", "")).strip().upper()
                if not src or not dst or src == dst:
                    continue
                key = (src, dst)
                agg[key]["count"] += 1
                amt = rows[i + 1].get("amount")
                if isinstance(amt, (int, float)):
                    agg[key]["amount"] += float(amt)
                if rows[i + 1].get("is_suspicious"):
                    agg[key]["suspicious"] += 1

    flows = []
    for (src, dst), meta in agg.items():
        slat, slon, _ = _coords(src)
        dlat, dlon, _ = _coords(dst)
        flows.append({
            "from": src,
            "to": dst,
            "from_lat": slat,
            "from_lon": slon,
            "to_lat": dlat,
            "to_lon": dlon,
            "amount": round(meta["amount"], 2),
            "suspicious": meta["suspicious"],
            "risk": "high" if meta["suspicious"] > 0 else "normal",
        })

    return sorted(flows, key=lambda f: (f["suspicious"], f["amount"]), reverse=True)[:24]


def render_globe(df, height: int = 520, version: int | None = None) -> None:
    """Globe bleu foncé avec contours pays + arcs de flux."""
    if version is None:
        version = int(time.time())

    signals = _country_signals(df)
    flows = _transfer_flows(df)
    signals_json = json.dumps(signals)
    flows_json = json.dumps(flows)
    cache_bust = f"{GLOBE_VERSION}-{version}"

    html = f"""
    <!-- globe {cache_bust} -->
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
          background: radial-gradient(ellipse at 50% 10%, #0a1e3d 0%, #010510 75%);
          overflow: hidden;
          font-family: system-ui, sans-serif;
        }}
        #wrap-{cache_bust} {{
          position: relative;
          width: 100%;
          height: {height}px;
        }}
        canvas {{
          width: 100%; height: 100%; display: block;
          touch-action: none;
          cursor: grab;
        }}
        canvas:active {{ cursor: grabbing; }}
        #hud-{cache_bust} {{
          position: absolute; top: 12px; left: 12px; z-index: 2;
          color: #38bdf8; font-size: 10px; letter-spacing: 0.14em;
          text-transform: uppercase; pointer-events: none;
        }}
        #hud-{cache_bust} strong {{
          display: block; color: #e0f2fe; font-size: 14px;
          text-transform: none; letter-spacing: 0.03em; margin-top: 3px;
        }}
        #legend-{cache_bust} {{
          position: absolute; bottom: 12px; left: 12px; z-index: 2;
          font-size: 10px; color: #7dd3fc; pointer-events: none;
          background: rgba(1, 10, 30, 0.85); padding: 8px 12px;
          border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.35);
          line-height: 1.8;
        }}
        .dot {{
          display: inline-block; width: 7px; height: 7px;
          border-radius: 50%; margin-right: 4px;
        }}
        .c-map {{ background: #0ea5e9; }}
        .c-flux {{ background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }}
        .c-warn {{ background: #f472b6; box-shadow: 0 0 6px #f472b6; }}
        #load-{cache_bust} {{
          position: absolute; inset: 0; display: flex;
          align-items: center; justify-content: center;
          color: #38bdf8; font-size: 12px; z-index: 5;
        }}
      </style>
    </head>
    <body>
      <div id="wrap-{cache_bust}">
        <div id="hud-{cache_bust}">
          Carte mondiale
          <strong>Bleu foncé · flux de transferts</strong>
          <span style="display:block;margin-top:6px;font-size:10px;color:#7dd3fc;
            letter-spacing:0.06em;text-transform:none;">
            Glisser pour tourner · molette/pincer pour zoomer
          </span>
        </div>
        <div id="load-{cache_bust}">Construction de la carte…</div>
        <canvas id="cv-{cache_bust}"></canvas>
        <div id="legend-{cache_bust}">
          <span><i class="dot c-map"></i>Contours pays (cyan)</span><br>
          <span><i class="dot c-flux"></i>Flux financier</span><br>
          <span><i class="dot c-warn"></i>Flux suspect</span>
        </div>
      </div>
      <script type="importmap">
        {{
          "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
          }}
        }}
      </script>
      <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

        const ID = "{cache_bust}";
        const signals = {signals_json};
        const flows = {flows_json};
        const GEO_URL = "{GEOJSON_URL}";

        const wrap = document.getElementById('wrap-' + ID);
        const canvas = document.getElementById('cv-' + ID);
        const loader = document.getElementById('load-' + ID);

        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x010510);

        const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
        camera.position.set(0, 0.25, 2.75);

        const globe = new THREE.Group();
        scene.add(globe);

        // ── Océan bleu foncé (pas de texture satellite) ──
        globe.add(new THREE.Mesh(
          new THREE.SphereGeometry(1, 72, 72),
          new THREE.MeshPhongMaterial({{
            color: 0x020d1f,
            emissive: 0x041a35,
            emissiveIntensity: 0.6,
            shininess: 4,
          }})
        ));

        // Graticule cyan
        globe.add(new THREE.LineSegments(
          new THREE.WireframeGeometry(new THREE.SphereGeometry(1.004, 40, 28)),
          new THREE.LineBasicMaterial({{ color: 0x0c4a6e, transparent: true, opacity: 0.55 }})
        ));

        function latLon(lat, lon, r) {{
          const phi = (90 - lat) * Math.PI / 180;
          const th  = (lon + 180) * Math.PI / 180;
          return new THREE.Vector3(
            -r * Math.sin(phi) * Math.cos(th),
             r * Math.cos(phi),
             r * Math.sin(phi) * Math.sin(th)
          );
        }}

        function arcCurve(la1, lo1, la2, lo2) {{
          const a = latLon(la1, lo1, 1.03);
          const b = latLon(la2, lo2, 1.03);
          const m = a.clone().add(b).multiplyScalar(0.5);
          m.normalize().multiplyScalar(1 + a.distanceTo(b) * 0.45);
          return new THREE.QuadraticBezierCurve3(a, m, b);
        }}

        // ── Contours pays (GeoJSON → traits cyan) ──
        async function drawMap() {{
          try {{
            const res = await fetch(GEO_URL);
            const geo = await res.json();
            const borderMat = new THREE.LineBasicMaterial({{
              color: 0x22d3ee, transparent: true, opacity: 0.9,
            }});
            const coastMat = new THREE.LineBasicMaterial({{
              color: 0x0ea5e9, transparent: true, opacity: 0.35,
            }});

            function addRing(ring, mat, r) {{
              if (!ring || ring.length < 2) return;
              const pts = ring.map(([lo, la]) => latLon(la, lo, r));
              const g = new THREE.BufferGeometry().setFromPoints(pts);
              globe.add(new THREE.Line(g, mat));
            }}

            geo.features.forEach(f => {{
              const g = f.geometry;
              if (g.type === 'Polygon') {{
                g.coordinates.forEach(ring => addRing(ring, borderMat, 1.012));
              }} else if (g.type === 'MultiPolygon') {{
                g.coordinates.forEach(poly => {{
                  poly.forEach(ring => addRing(ring, borderMat, 1.012));
                }});
              }}
            }});

            // Second contour plus large (effet carte)
            geo.features.forEach(f => {{
              const g = f.geometry;
              if (g.type === 'Polygon') {{
                g.coordinates.forEach(ring => addRing(ring, coastMat, 1.006));
              }} else if (g.type === 'MultiPolygon') {{
                g.coordinates.forEach(poly => {{
                  poly.forEach(ring => addRing(ring, coastMat, 1.006));
                }});
              }}
            }});
          }} catch (e) {{
            console.warn('GeoJSON fallback', e);
            // Fallback : sphère cyan wireframe dense
            globe.add(new THREE.LineSegments(
              new THREE.WireframeGeometry(new THREE.SphereGeometry(1.01, 48, 32)),
              new THREE.LineBasicMaterial({{ color: 0x22d3ee, opacity: 0.5, transparent: true }})
            ));
          }}
          loader.style.display = 'none';
        }}

        // ── Flux de transfert (tubes lumineux + particules) ──
        const flowAnim = [];
        const colors = {{ normal: 0x38bdf8, high: 0xf472b6 }};

        flows.forEach((f, i) => {{
          const col = colors[f.risk] || colors.normal;
          const curve = arcCurve(f.from_lat, f.from_lon, f.to_lat, f.to_lon);
          const tubularSegments = 80;
          const tubeR = f.risk === 'high' ? 0.006 : 0.004;

          const tube = new THREE.TubeGeometry(curve, tubularSegments, tubeR, 6, false);
          globe.add(new THREE.Mesh(tube, new THREE.MeshBasicMaterial({{
            color: col, transparent: true, opacity: f.risk === 'high' ? 0.85 : 0.55,
          }})));

          // Halo autour du tube
          const tube2 = new THREE.TubeGeometry(curve, tubularSegments, tubeR * 2.5, 6, false);
          globe.add(new THREE.Mesh(tube2, new THREE.MeshBasicMaterial({{
            color: col, transparent: true, opacity: 0.12,
          }})));

          const nDots = f.risk === 'high' ? 5 : 3;
          for (let d = 0; d < nDots; d++) {{
            const dot = new THREE.Mesh(
              new THREE.SphereGeometry(0.016, 10, 10),
              new THREE.MeshBasicMaterial({{ color: 0xffffff }})
            );
            globe.add(dot);
            flowAnim.push({{ curve, dot, off: d / nDots + i * 0.1, spd: 0.2 + d * 0.03 }});
          }}
        }});

        // ── Signaux pays ──
        const pins = [];
        const pinCol = {{ high: 0xf87171, medium: 0xfbbf24, low: 0x38bdf8 }};
        signals.forEach((s, i) => {{
          const c = pinCol[s.risk] || pinCol.low;
          const p = latLon(s.lat, s.lon, 1.02);
          const sz = s.risk === 'high' ? 0.03 : 0.02;
          const pin = new THREE.Mesh(
            new THREE.SphereGeometry(sz, 14, 14),
            new THREE.MeshBasicMaterial({{ color: c }})
          );
          pin.position.copy(p);
          globe.add(pin);
          pins.push({{ pin, i, risk: s.risk }});
        }});

        // Atmosphère
        globe.add(new THREE.Mesh(
          new THREE.SphereGeometry(1.09, 40, 40),
          new THREE.MeshBasicMaterial({{
            color: 0x0284c7, transparent: true, opacity: 0.04, side: THREE.BackSide,
          }})
        ));

        scene.add(new THREE.AmbientLight(0x0c4a6e, 1.2));
        const dl = new THREE.DirectionalLight(0x38bdf8, 0.8);
        dl.position.set(3, 2, 4);
        scene.add(dl);

        // Contrôles souris + tactile
        const controls = new OrbitControls(camera, canvas);
        controls.target.set(0, 0, 0);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.rotateSpeed = 0.7;
        controls.enablePan = false;
        controls.minDistance = 1.55;
        controls.maxDistance = 4.2;
        controls.enableZoom = true;
        controls.autoRotate = false;
        controls.touches = {{ ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN }};

        let userDragging = false;
        controls.addEventListener('start', () => {{ userDragging = true; }});
        controls.addEventListener('end', () => {{ userDragging = false; }});

        function resize() {{
          const w = wrap.clientWidth, h = wrap.clientHeight;
          renderer.setSize(w, h, false);
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
        }}
        resize();
        window.addEventListener('resize', resize);

        let t = 0;
        function loop() {{
          requestAnimationFrame(loop);
          t += 0.007;

          // Rotation automatique sur lui-même (ralentit pendant le toucher)
          const spin = userDragging ? 0.001 : 0.004;
          globe.rotation.y += spin;
          globe.rotation.x = Math.sin(t * 0.15) * 0.03;

          controls.update();

          flowAnim.forEach(f => {{
            f.dot.position.copy(f.curve.getPoint((t * f.spd + f.off) % 1));
          }});

          pins.forEach(p => {{
            if (p.risk !== 'low') {{
              const s = 1 + 0.3 * Math.sin(t * 3 + p.i);
              p.pin.scale.setScalar(s);
            }}
          }});

          renderer.render(scene, camera);
        }}

        drawMap().then(() => loop());
      </script>
    </body>
    </html>
    """

    components.html(html, height=height + 12, scrolling=False)
