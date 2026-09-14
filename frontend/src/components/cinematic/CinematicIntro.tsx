import React, { useEffect, useRef, useState, useCallback } from 'react';
import './CinematicIntro.css';

// ═══════════════════════════════════════════════════════
// CINEMATIC INTRO — "The Intelligence Field"
// KnowUrDB signature opening experience
//
// Architecture:
//   ONE master RAF loop → ONE progress variable (0→1)
//   Canvas: particles, atmosphere, lens arcs, optical pulse
//   DOM: wordmark, subtitle, signal path (crisp subpixel text)
//
// StrictMode-safe: all mutable state in refs, proper cleanup
// ═══════════════════════════════════════════════════════

interface CinematicIntroProps {
  onReveal: () => void;
  onComplete: () => void;
}

// ─── Particle type ───
interface FieldParticle {
  x: number;
  y: number;
  originX: number;
  originY: number;
  vx: number;
  vy: number;
  radius: number;
  alpha: number;
  maxAlpha: number;
  depth: number; // 0=far, 1=mid, 2=near
  hue: number;
  phase: number; // individual phase offset for organic movement
  arcAngle: number; // for convergence arc trajectories
  arcRadius: number;
}

// ─── Easing functions ───
const easeOutCubic = (t: number): number => 1 - Math.pow(1 - t, 3);
const easeInOutCubic = (t: number): number =>
  t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const easeInOutQuart = (t: number): number =>
  t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2;
const easeOutQuint = (t: number): number => 1 - Math.pow(1 - t, 5);
const easeInQuad = (t: number): number => t * t;

// Clamp helper
const clamp = (v: number, min: number, max: number): number =>
  v < min ? min : v > max ? max : v;

// Phase progress helper: returns 0→1 for progress within [start, start+duration]
const phaseProgress = (progress: number, start: number, duration: number): number =>
  clamp((progress - start) / duration, 0, 1);

export const CinematicIntro: React.FC<CinematicIntroProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wordmarkRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const signalPathRef = useRef<HTMLDivElement>(null);
  const signalActiveRef = useRef<HTMLDivElement>(null);
  const signalHeadRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const [isExit, setIsExit] = useState(false);

  // Stable callback refs (prevent re-triggering the effect)
  const onRevealRef = useRef(onReveal);
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onRevealRef.current = onReveal;
    onCompleteRef.current = onComplete;
  }, [onReveal, onComplete]);

  // Reduced motion detection
  const reducedMotionRef = useRef(false);
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotionRef.current = mq.matches;
    const handler = (e: MediaQueryListEvent) => { reducedMotionRef.current = e.matches; };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  // Scroll lock
  useEffect(() => {
    document.documentElement.classList.add('lock-scroll');
    document.body.classList.add('lock-scroll');
    const top = window.scrollY;
    const block = (e: Event) => { e.preventDefault(); window.scrollTo(0, top); };
    window.addEventListener('scroll', block, { passive: false });
    window.addEventListener('wheel', block, { passive: false });
    window.addEventListener('touchmove', block, { passive: false });
    return () => {
      document.documentElement.classList.remove('lock-scroll');
      document.body.classList.remove('lock-scroll');
      window.removeEventListener('scroll', block);
      window.removeEventListener('wheel', block);
      window.removeEventListener('touchmove', block);
    };
  }, []);

  // Exit trigger
  const triggerExit = useCallback(() => {
    setIsExit(true);
    setTimeout(() => onRevealRef.current(), 350);
    setTimeout(() => onCompleteRef.current(), 1000);
  }, []);

  // ═══════════════════════════════════════════════════════
  // MASTER CINEMATIC ENGINE
  // ═══════════════════════════════════════════════════════
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const TOTAL_DURATION = 3100; // ms — ~3.1 seconds
    const REDUCED_DURATION = 1200; // ms for reduced motion

    // Mutable refs for RAF
    let rAF = 0;
    let startTime = 0;
    let particles: FieldParticle[] = [];
    let cx = 0;
    let cy = 0;
    let w = 0;
    let h = 0;

    // ─── Canvas resize ───
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = w / 2;
      cy = h / 2;
      initParticles();
    };

    // ─── Particle initialization ───
    const initParticles = () => {
      particles = [];
      const isMobile = w < 768;
      const isTablet = w >= 768 && w < 1024;
      const count = isMobile ? 50 : isTablet ? 80 : 120;
      const maxDist = Math.max(cx, cy) * 0.95;

      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dist = 60 + Math.random() * maxDist;
        const x = cx + Math.cos(angle) * dist;
        const y = cy + Math.sin(angle) * dist;
        const rand = Math.random();
        const depth = rand > 0.85 ? 2 : rand > 0.45 ? 1 : 0;

        particles.push({
          x, y,
          originX: x,
          originY: y,
          vx: (Math.random() - 0.5) * 0.12,
          vy: (Math.random() - 0.5) * 0.12,
          radius: depth === 2 ? 1.0 + Math.random() * 0.5
                : depth === 1 ? 0.5 + Math.random() * 0.35
                : 0.2 + Math.random() * 0.25,
          alpha: 0,
          maxAlpha: depth === 2 ? 0.5 + Math.random() * 0.3
                  : depth === 1 ? 0.18 + Math.random() * 0.15
                  : 0.06 + Math.random() * 0.08,
          depth,
          hue: 180 + Math.random() * 12,
          phase: Math.random() * Math.PI * 2,
          arcAngle: angle,
          arcRadius: dist,
        });
      }
    };

    // ─── Atmosphere rendering ───
    const renderAtmosphere = (progress: number) => {
      // Phase: 0.0 → 0.12 atmosphere emergence
      const atmosP = easeOutCubic(phaseProgress(progress, 0, 0.12));
      const baseAlpha = atmosP * 0.14;

      // Deep navy radial
      const navyGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) * 0.6);
      navyGrad.addColorStop(0, `rgba(4, 30, 50, ${baseAlpha})`);
      navyGrad.addColorStop(0.5, `rgba(6, 12, 30, ${baseAlpha * 0.6})`);
      navyGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = navyGrad;
      ctx.fillRect(0, 0, w, h);

      // Extremely subtle purple atmospheric layer
      const purpleAlpha = baseAlpha * 0.35;
      const purpleGrad = ctx.createRadialGradient(
        cx + w * 0.15, cy - h * 0.1, 0,
        cx + w * 0.15, cy - h * 0.1, Math.max(w, h) * 0.5
      );
      purpleGrad.addColorStop(0, `rgba(30, 8, 50, ${purpleAlpha})`);
      purpleGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = purpleGrad;
      ctx.fillRect(0, 0, w, h);

      // Convergence brightening: atmosphere intensifies during ACT III
      const convergeAtmos = easeInOutCubic(phaseProgress(progress, 0.35, 0.25));
      if (convergeAtmos > 0) {
        const intenseGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) * 0.45);
        intenseGrad.addColorStop(0, `rgba(6, 60, 80, ${convergeAtmos * 0.08})`);
        intenseGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = intenseGrad;
        ctx.fillRect(0, 0, w, h);
      }
    };

    // ─── Particle rendering ───
    const renderParticles = (progress: number, time: number) => {
      // Data field emergence: 0.05 → 0.35
      const fieldAlpha = easeOutCubic(phaseProgress(progress, 0.05, 0.3));
      // Convergence: 0.30 → 0.60
      const convergeStrength = easeInOutQuart(phaseProgress(progress, 0.30, 0.30));
      // Focus stillness: particles slow down near 0.62–0.66
      const focusPause = progress > 0.60 && progress < 0.68
        ? 1 - Math.sin(phaseProgress(progress, 0.60, 0.08) * Math.PI) * 0.85
        : 1;
      // Post-reveal fade: 0.75 → 0.95
      const postFade = progress > 0.75 ? 1 - easeInQuad(phaseProgress(progress, 0.75, 0.20)) * 0.65 : 1;
      // Optical pulse influence
      const pulseP = phaseProgress(progress, 0.64, 0.08);
      const pulseActive = pulseP > 0 && pulseP < 1;
      const pulseSin = pulseActive ? Math.sin(pulseP * Math.PI) : 0;

      for (const p of particles) {
        // Convergence target
        const dx = cx - p.originX;
        const dy = cy - p.originY;
        const convergeX = p.originX + dx * convergeStrength * 0.75;
        const convergeY = p.originY + dy * convergeStrength * 0.75;

        // Gentle organic drift
        const driftScale = focusPause;
        p.x += p.vx * driftScale;
        p.y += p.vy * driftScale;

        // Subtle sinusoidal organic movement
        const sinOffset = Math.sin(time * 0.0008 + p.phase) * 0.3 * driftScale;
        const cosOffset = Math.cos(time * 0.0006 + p.phase * 1.3) * 0.2 * driftScale;
        p.x += sinOffset;
        p.y += cosOffset;

        // Lerp toward converged position
        const lerpSpeed = 0.015 + convergeStrength * 0.055;
        p.x += (convergeX - p.x) * lerpSpeed;
        p.y += (convergeY - p.y) * lerpSpeed;

        // Alpha: field emergence × post-fade
        p.alpha = p.maxAlpha * fieldAlpha * postFade;

        // Pulse brightening for nearby particles
        if (pulseActive) {
          const distToCenter = Math.hypot(p.x - cx, p.y - cy);
          const pulseInfluence = Math.max(0, 1 - distToCenter / 280);
          p.alpha += pulseInfluence * pulseSin * 0.25;

          // Slight outward push during pulse (refraction)
          if (distToCenter > 5) {
            const pushStrength = pulseInfluence * pulseSin * 1.5;
            const pushAngle = Math.atan2(p.y - cy, p.x - cx);
            p.x += Math.cos(pushAngle) * pushStrength;
            p.y += Math.sin(pushAngle) * pushStrength;
          }
        }

        if (p.alpha < 0.004) continue;

        // Draw particle
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        if (p.depth === 2) {
          ctx.fillStyle = `hsla(${p.hue}, 75%, 65%, ${p.alpha})`;
        } else if (p.depth === 1) {
          ctx.fillStyle = `rgba(180, 200, 220, ${p.alpha})`;
        } else {
          ctx.fillStyle = `rgba(100, 110, 140, ${p.alpha * 0.8})`;
        }
        ctx.fill();

        // Near-layer particles: soft glow
        if (p.depth === 2 && p.alpha > 0.12) {
          const gr = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 5);
          gr.addColorStop(0, `hsla(${p.hue}, 75%, 65%, ${p.alpha * 0.2})`);
          gr.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = gr;
          ctx.fillRect(p.x - p.radius * 5, p.y - p.radius * 5, p.radius * 10, p.radius * 10);
        }

        // Mid-layer signal traces during convergence
        if (p.depth === 1 && convergeStrength > 0.3 && p.alpha > 0.08) {
          const traceLen = convergeStrength * 12;
          const angle = Math.atan2(cy - p.y, cx - p.x);
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x - Math.cos(angle) * traceLen, p.y - Math.sin(angle) * traceLen);
          ctx.strokeStyle = `rgba(34, 211, 238, ${p.alpha * 0.3 * convergeStrength})`;
          ctx.lineWidth = 0.4;
          ctx.stroke();
        }
      }
    };

    // ─── Intelligence lens rendering ───
    const renderLens = (progress: number, time: number) => {
      // Lens emergence: 0.40 → 0.62
      const lensP = easeInOutQuart(phaseProgress(progress, 0.40, 0.22));
      if (lensP < 0.01) return;

      // Lens fade after reveal: 0.72 → 0.88
      const lensFade = progress > 0.72 ? Math.max(0, 1 - phaseProgress(progress, 0.72, 0.16)) : 1;
      const lensAlpha = lensP * lensFade;

      const isMobile = w < 768;
      const baseRadius = isMobile ? 55 : w < 1024 ? 75 : 95;

      // Arc segments — 3 arcs at different radii, with directional rotation
      const arcs = [
        { radius: baseRadius * 1.0, startAngle: -0.3, arcLen: 1.8, rotSpeed: 0.15, width: 0.5, alphaScale: 0.3 },
        { radius: baseRadius * 0.65, startAngle: 1.5, arcLen: 1.4, rotSpeed: -0.1, width: 0.4, alphaScale: 0.25 },
        { radius: baseRadius * 0.38, startAngle: 3.2, arcLen: 1.0, rotSpeed: 0.08, width: 0.35, alphaScale: 0.2 },
      ];

      for (const arc of arcs) {
        const growFactor = Math.min(lensP * 1.5, 1); // arcs grow in
        const rotation = time * 0.001 * arc.rotSpeed;
        const start = arc.startAngle + rotation;
        const end = start + arc.arcLen * growFactor;

        ctx.beginPath();
        ctx.arc(cx, cy, arc.radius, start, end);
        ctx.strokeStyle = `rgba(34, 211, 238, ${lensAlpha * arc.alphaScale})`;
        ctx.lineWidth = arc.width;
        ctx.stroke();
      }

      // Soft core glow
      const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, baseRadius * 0.4);
      coreGrad.addColorStop(0, `rgba(34, 211, 238, ${lensAlpha * 0.08})`);
      coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = coreGrad;
      ctx.fillRect(cx - baseRadius, cy - baseRadius, baseRadius * 2, baseRadius * 2);
    };

    // ─── Optical pulse (focus event) ───
    const renderOpticalPulse = (progress: number) => {
      // Pulse: 0.64 → 0.72
      const pulseP = phaseProgress(progress, 0.64, 0.08);
      if (pulseP <= 0 || pulseP >= 1) return;

      const pulseSin = Math.sin(pulseP * Math.PI);
      const pulseRadius = 15 + easeOutCubic(pulseP) * 250;

      // Main pulse wave
      const pulseGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, pulseRadius);
      pulseGrad.addColorStop(0, `rgba(34, 211, 238, ${pulseSin * 0.2})`);
      pulseGrad.addColorStop(0.35, `rgba(34, 211, 238, ${pulseSin * 0.08})`);
      pulseGrad.addColorStop(0.7, `rgba(34, 211, 238, ${pulseSin * 0.02})`);
      pulseGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = pulseGrad;
      ctx.fillRect(0, 0, w, h);

      // Thin wavefront ring at the edge of the pulse
      if (pulseP > 0.15 && pulseP < 0.85) {
        const ringAlpha = Math.sin((pulseP - 0.15) / 0.7 * Math.PI) * 0.15;
        ctx.beginPath();
        ctx.arc(cx, cy, pulseRadius * 0.9, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(34, 211, 238, ${ringAlpha})`;
        ctx.lineWidth = 0.6;
        ctx.stroke();
      }
    };

    // ─── Camera drift (applied to canvas transform) ───
    const applyCameraDrift = (time: number, progress: number) => {
      // Subtle drift, strongest during convergence
      const driftIntensity = progress < 0.2 ? easeOutCubic(progress / 0.2) * 0.5
                           : progress > 0.8 ? 1 - easeOutCubic((progress - 0.8) / 0.2)
                           : 1;
      const driftX = Math.sin(time * 0.0003) * 1.5 * driftIntensity;
      const driftY = Math.cos(time * 0.00025) * 1.0 * driftIntensity;
      const driftScale = 1 + Math.sin(time * 0.0002) * 0.003 * driftIntensity;
      canvas.style.transform = `translate(${driftX}px, ${driftY}px) scale(${driftScale})`;
    };

    // ─── DOM element updates (wordmark, subtitle, signal path) ───
    const updateDOM = (progress: number) => {
      const wordmark = wordmarkRef.current;
      const subtitle = subtitleRef.current;
      const signalPath = signalPathRef.current;
      const signalActive = signalActiveRef.current;
      const signalHead = signalHeadRef.current;

      // WORDMARK: resolve from blurry→sharp (0.52 → 0.74)
      if (wordmark) {
        const wordP = phaseProgress(progress, 0.52, 0.22);
        const wordEased = easeOutQuint(wordP);

        if (wordP <= 0) {
          wordmark.style.opacity = '0';
          wordmark.style.filter = 'blur(12px)';
        } else {
          const blur = (1 - wordEased) * 10;
          const opacity = easeOutCubic(wordP);

          // Color: starts cyan-tinted → resolves to zinc-100
          const cyanInfluence = Math.max(0, 1 - wordEased * 1.8);
          const textShadow = cyanInfluence > 0.05
            ? `0 0 ${30 * cyanInfluence}px rgba(34, 211, 238, ${cyanInfluence * 0.25})`
            : 'none';

          wordmark.style.opacity = `${opacity}`;
          wordmark.style.filter = blur > 0.3 ? `blur(${blur}px)` : 'none';
          wordmark.style.textShadow = textShadow;
        }
      }

      // SUBTITLE: resolve from blurry→sharp (0.68 → 0.86)
      if (subtitle) {
        const subP = phaseProgress(progress, 0.68, 0.18);
        const subEased = easeOutCubic(subP);

        if (subP <= 0) {
          subtitle.style.opacity = '0';
          subtitle.style.filter = 'blur(6px)';
          subtitle.style.transform = 'translateY(6px)';
        } else {
          const blur = (1 - subEased) * 5;
          const translateY = (1 - subEased) * 5;

          subtitle.style.opacity = `${easeOutCubic(subP)}`;
          subtitle.style.filter = blur > 0.3 ? `blur(${blur}px)` : 'none';
          subtitle.style.transform = `translateY(${translateY}px)`;
        }
      }

      // SIGNAL PATH: emerges at 0.15, tracks progress, fades at 0.90
      if (signalPath && signalActive && signalHead) {
        const pathAppear = easeOutCubic(phaseProgress(progress, 0.15, 0.08));
        const pathProgress = easeInOutCubic(phaseProgress(progress, 0.15, 0.72));
        const pathFade = progress > 0.90 ? 1 - phaseProgress(progress, 0.90, 0.08) : 1;

        signalPath.style.opacity = `${pathAppear * pathFade}`;
        signalActive.style.width = `${pathProgress * 100}%`;
        signalHead.style.left = `${pathProgress * 100}%`;
        signalHead.style.opacity = pathProgress > 0.01 && pathProgress < 0.99 ? '1' : '0';
      }
    };

    // ═══════════════════════════════════════════════════════
    // MAIN ANIMATION FRAME
    // ═══════════════════════════════════════════════════════
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / TOTAL_DURATION, 1);

      ctx.clearRect(0, 0, w, h);

      // Canvas rendering
      renderAtmosphere(progress);
      renderParticles(progress, elapsed);
      renderLens(progress, elapsed);
      renderOpticalPulse(progress);

      // Camera drift
      applyCameraDrift(elapsed, progress);

      // DOM updates (wordmark, subtitle, signal)
      updateDOM(progress);

      // Global exit dim (0.93 → 1.0)
      if (progress > 0.93) {
        const exitDim = easeInOutCubic(phaseProgress(progress, 0.93, 0.07));
        ctx.fillStyle = `rgba(2, 2, 4, ${exitDim * 0.3})`;
        ctx.fillRect(0, 0, w, h);
      }

      // Continue or trigger exit
      if (progress < 1) {
        rAF = requestAnimationFrame(animate);
      } else {
        triggerExit();
      }
    };

    // ─── Reduced motion path ───
    const animateReduced = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / REDUCED_DURATION, 1);

      ctx.clearRect(0, 0, w, h);

      // Simple atmosphere
      const atmosAlpha = easeOutCubic(Math.min(progress / 0.3, 1)) * 0.1;
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) * 0.5);
      grad.addColorStop(0, `rgba(4, 30, 50, ${atmosAlpha})`);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Show wordmark immediately with opacity
      const wordmark = wordmarkRef.current;
      const subtitle = subtitleRef.current;
      const signalPath = signalPathRef.current;
      const signalActive = signalActiveRef.current;
      const signalHead = signalHeadRef.current;

      if (wordmark) {
        const alpha = easeOutCubic(Math.min(progress / 0.5, 1));
        wordmark.style.opacity = `${alpha}`;
        wordmark.style.filter = 'none';
        wordmark.style.textShadow = 'none';
      }
      if (subtitle) {
        const alpha = easeOutCubic(Math.max(0, (progress - 0.25) / 0.4));
        subtitle.style.opacity = `${alpha}`;
        subtitle.style.filter = 'none';
        subtitle.style.transform = 'translateY(0)';
      }
      if (signalPath && signalActive && signalHead) {
        signalPath.style.opacity = `${easeOutCubic(Math.min(progress / 0.3, 1))}`;
        signalActive.style.width = `${easeInOutCubic(progress) * 100}%`;
        signalHead.style.left = `${easeInOutCubic(progress) * 100}%`;
        signalHead.style.opacity = progress > 0.05 && progress < 0.95 ? '1' : '0';
      }

      if (progress < 1) {
        rAF = requestAnimationFrame(animateReduced);
      } else {
        triggerExit();
      }
    };

    // ─── Initialize and start ───
    window.addEventListener('resize', resize);
    resize();
    rAF = requestAnimationFrame(reducedMotionRef.current ? animateReduced : animate);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(rAF);
    };
  }, [triggerExit]);

  return (
    <div
      ref={rootRef}
      className={`cinematic-root${isExit ? ' cinematic-exit' : ''}`}
      aria-live="polite"
      aria-label="Loading KnowUrDB"
      role="status"
    >
      {/* Film grain texture */}
      <div className="cinematic-grain" />

      {/* The cinematic canvas — particles, atmosphere, lens, pulse */}
      <canvas ref={canvasRef} className="cinematic-canvas" />

      {/* DOM overlay — crisp text rendering */}
      <div className="cinematic-overlay">
        <h1 ref={wordmarkRef} className="cinematic-wordmark">
          KnowUrDB
        </h1>
        <p ref={subtitleRef} className="cinematic-subtitle">
          Turn questions into clarity.
        </p>
        <div ref={signalPathRef} className="cinematic-signal-path">
          <div className="cinematic-signal-base" />
          <div ref={signalActiveRef} className="cinematic-signal-active" />
          <div ref={signalHeadRef} className="cinematic-signal-head" />
        </div>
      </div>
    </div>
  );
};
