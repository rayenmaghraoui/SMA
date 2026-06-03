/**
 * ParticleField3D — fond animé avec particules en perspective (effet tunnel + constellation).
 * Monté une seule fois dans App.jsx en position fixed derrière tout le contenu.
 */

import { useRef, useEffect } from 'react';

const ParticleField3D = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    const resize = () => {
      canvas.width  = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const NUM      = 130;
    const FOCAL    = 340;
    const MAX_Z    = 1600;
    const SPREAD   = 2800;
    const CONN_MAX = 75;
    const CONN_SQ  = CONN_MAX * CONN_MAX;

    const mkParticle = () => ({
      x:     (Math.random() - 0.5) * SPREAD,
      y:     (Math.random() - 0.5) * SPREAD,
      z:     Math.random() * MAX_Z + 40,
      speed: 0.9 + Math.random() * 1.5,
    });

    const particles = Array.from({ length: NUM }, mkParticle);

    const draw = () => {
      const w  = canvas.width;
      const h  = canvas.height;
      const cx = w / 2;
      const cy = h / 2;

      ctx.clearRect(0, 0, w, h);

      /* — Projection perspective + dessin des particules — */
      const pts = [];

      particles.forEach((p) => {
        p.z -= p.speed;
        if (p.z <= 1) {
          Object.assign(p, mkParticle());
          p.z = MAX_Z;
        }

        const scale = FOCAL / p.z;
        const sx    = p.x * scale + cx;
        const sy    = p.y * scale + cy;

        if (sx < -120 || sx > w + 120 || sy < -120 || sy > h + 120) {
          pts.push(null);
          return;
        }

        const depth = Math.max(0, 1 - p.z / MAX_Z);   // 0 = très loin, 1 = très proche
        const size  = Math.max(0.3, depth * 2.8);
        const alpha = Math.min(0.92, depth * 1.6);

        /* violet profond lointain → blanc pur proche */
        const r = Math.round(139 + depth * 116);
        const g = Math.round(92  + depth * 163);
        const b = 246;

        ctx.beginPath();
        ctx.arc(sx, sy, size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
        ctx.fill();

        pts.push({ sx, sy, depth });
      });

      /* — Lignes constellation entre particules projetées proches — */
      for (let a = 0; a < pts.length - 1; a++) {
        const pa = pts[a];
        if (!pa || pa.depth < 0.18) continue;
        for (let b = a + 1; b < pts.length; b++) {
          const pb = pts[b];
          if (!pb || pb.depth < 0.18) continue;
          const dx = pa.sx - pb.sx;
          const dy = pa.sy - pb.sy;
          const d2 = dx * dx + dy * dy;
          if (d2 < CONN_SQ) {
            const t         = 1 - Math.sqrt(d2) / CONN_MAX;
            const lineAlpha = t * 0.17 * ((pa.depth + pb.depth) * 0.5);
            ctx.beginPath();
            ctx.moveTo(pa.sx, pa.sy);
            ctx.lineTo(pb.sx, pb.sy);
            ctx.strokeStyle = `rgba(167,139,250,${lineAlpha.toFixed(3)})`;
            ctx.lineWidth   = 0.5;
            ctx.stroke();
          }
        }
      }

      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
      ro.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="w-full h-full pointer-events-none"
    />
  );
};

export default ParticleField3D;
