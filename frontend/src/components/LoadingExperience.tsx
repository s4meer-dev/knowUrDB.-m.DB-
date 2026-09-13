import React, { useEffect, useRef, useState, useCallback } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

// ─── Particle type for the intelligence data field ───
interface DataParticle {
  x: number;
  y: number;
  originX: number;
  originY: number;
  vx: number;
  vy: number;
  radius: number;
  alpha: number;
  maxAlpha: number;
  layer: number; // 1=far, 2=mid, 3=near
  hue: number; // cyan spectrum
}

// ─── Easing functions ───
const easeOutCubic = (x: number): number => 1 - Math.pow(1 - x, 3);
const easeInOutQuart = (x: number): number =>
  x < 0.5 ? 8 * x * x * x * x : 1 - Math.pow(-2 * x + 2, 4) / 2;
const easeInOutCubic = (x: number): number =>
  x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const easeOutQuint = (x: number): number => 1 - Math.pow(1 - x, 5);

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [isExit, setIsExit] = useState(false);

  // Stable callback refs
  const onRevealRef = useRef(onReveal);
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onRevealRef.current = onReveal;
    onCompleteRef.current = onComplete;
  }, [onReveal, onComplete]);

  // Reduced motion detection
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
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

  // ─── Cinematic exit trigger ───
  const triggerExit = useCallback(() => {
    setIsExit(true);
    setTimeout(() => onRevealRef.current(), 350);
    setTimeout(() => onCompleteRef.current(), 1000);
  }, []);

  // ═══════════════════════════════════════════════════════
  // MAIN CINEMATIC ENGINE — single canvas + single RAF
  // ═══════════════════════════════════════════════════════
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const TOTAL_DURATION = 3200; // 3.2 seconds
    let rAF = 0;
    let startTime = 0;
    let particles: DataParticle[] = [];
    let cx = 0;
    let cy = 0;
    let dpr = 1;

    // ─── Setup ───
    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = window.innerWidth / 2;
      cy = window.innerHeight / 2;
      initParticles();
    };

    const initParticles = () => {
      particles = [];
      const isMobile = window.innerWidth < 768;
      const count = isMobile ? 60 : 150;

      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dist = 80 + Math.random() * Math.max(cx, cy) * 0.9;
        const x = cx + Math.cos(angle) * dist;
        const y = cy + Math.sin(angle) * dist;
        const rand = Math.random();
        const layer = rand > 0.88 ? 3 : rand > 0.5 ? 2 : 1;

        particles.push({
          x, y,
          originX: x,
          originY: y,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          radius: layer === 3 ? 1.2 + Math.random() * 0.6 : layer === 2 ? 0.6 + Math.random() * 0.4 : 0.3 + Math.random() * 0.3,
          alpha: 0,
          maxAlpha: layer === 3 ? 0.6 + Math.random() * 0.3 : layer === 2 ? 0.25 + Math.random() * 0.2 : 0.08 + Math.random() * 0.1,
          layer,
          hue: 180 + Math.random() * 15, // cyan range
        });
      }
    };

    // ─── Text measurement helper ───
    const measureText = (text: string, fontSize: number, fontWeight: string) => {
      ctx.save();
      ctx.font = `${fontWeight} ${fontSize}px Inter, -apple-system, sans-serif`;
      const m = ctx.measureText(text);
      ctx.restore();
      return m.width;
    };

    // ─── Main animation frame ───
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / TOTAL_DURATION, 1);
      const w = window.innerWidth;
      const h = window.innerHeight;

      ctx.clearRect(0, 0, w, h);

      // ════════════════════════════════════
      // PHASE 1: Atmosphere (0% → 15%)
      // Deep radial atmosphere fading in
      // ════════════════════════════════════
      const atmosP = Math.min(progress / 0.15, 1);
      const atmosAlpha = easeOutCubic(atmosP) * 0.18;
      const atmosGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) * 0.65);
      atmosGrad.addColorStop(0, `rgba(6, 90, 110, ${atmosAlpha})`);
      atmosGrad.addColorStop(0.35, `rgba(20, 8, 50, ${atmosAlpha * 0.6})`);
      atmosGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = atmosGrad;
      ctx.fillRect(0, 0, w, h);

      // ════════════════════════════════════
      // PHASE 2: Data field emerges (5% → 40%)
      // Particles appear and begin drifting
      // ════════════════════════════════════
      const fieldAppearP = progress < 0.05 ? 0 : Math.min((progress - 0.05) / 0.35, 1);
      const fieldAlpha = easeOutCubic(fieldAppearP);

      // ════════════════════════════════════
      // PHASE 3: Convergence (25% → 55%)
      // Particles bend toward center
      // ════════════════════════════════════
      const convergeP = progress < 0.25 ? 0 : Math.min((progress - 0.25) / 0.3, 1);
      const convergeStrength = easeInOutCubic(convergeP);

      // ════════════════════════════════════
      // PHASE 4: Intelligence lens (40% → 60%)
      // Central ring structure forms
      // ════════════════════════════════════
      const lensP = progress < 0.4 ? 0 : Math.min((progress - 0.4) / 0.2, 1);
      const lensAlpha = easeInOutQuart(lensP);

      // Draw lens rings
      if (lensAlpha > 0.01) {
        const isMobile = w < 768;
        const lensRadius = isMobile ? 60 : 100;
        const fadeOut = progress > 0.65 ? Math.max(0, 1 - (progress - 0.65) / 0.15) : 1;
        const ringAlpha = lensAlpha * fadeOut;

        // Outer ring — extremely thin
        ctx.beginPath();
        ctx.arc(cx, cy, lensRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(34, 211, 238, ${ringAlpha * 0.25})`;
        ctx.lineWidth = 0.6;
        ctx.stroke();

        // Inner ring
        ctx.beginPath();
        ctx.arc(cx, cy, lensRadius * 0.55, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(34, 211, 238, ${ringAlpha * 0.35})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();

        // Core point
        const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, lensRadius * 0.35);
        coreGrad.addColorStop(0, `rgba(34, 211, 238, ${ringAlpha * 0.12})`);
        coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = coreGrad;
        ctx.fillRect(cx - lensRadius, cy - lensRadius, lensRadius * 2, lensRadius * 2);
      }

      // ════════════════════════════════════
      // PHASE 5: Aqua pulse (50% → 58%)
      // A controlled optical pulse through the focal plane
      // ════════════════════════════════════
      const pulseP = progress < 0.5 ? 0 : Math.min((progress - 0.5) / 0.08, 1);
      if (pulseP > 0 && pulseP < 1) {
        const pulseEased = Math.sin(pulseP * Math.PI);
        const pulseRadius = 20 + pulseEased * 220;
        const pulseGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, pulseRadius);
        pulseGrad.addColorStop(0, `rgba(34, 211, 238, ${pulseEased * 0.28})`);
        pulseGrad.addColorStop(0.4, `rgba(34, 211, 238, ${pulseEased * 0.1})`);
        pulseGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = pulseGrad;
        ctx.fillRect(0, 0, w, h);
      }

      // ════════════════════════════════════
      // Draw particles with convergence
      // ════════════════════════════════════
      for (const p of particles) {
        // Target: converge toward center
        const dx = cx - p.originX;
        const dy = cy - p.originY;
        const targetX = p.originX + dx * convergeStrength * 0.7;
        const targetY = p.originY + dy * convergeStrength * 0.7;

        // Gentle drift
        p.x += p.vx;
        p.y += p.vy;

        // Lerp toward converged position
        const lerpFactor = 0.02 + convergeStrength * 0.06;
        p.x += (targetX - p.x) * lerpFactor;
        p.y += (targetY - p.y) * lerpFactor;

        // Particle alpha
        p.alpha = p.maxAlpha * fieldAlpha;

        // During pulse, nearby particles get brighter
        if (pulseP > 0 && pulseP < 1) {
          const distToCenter = Math.hypot(p.x - cx, p.y - cy);
          const pulseInfluence = Math.max(0, 1 - distToCenter / 250);
          p.alpha += pulseInfluence * Math.sin(pulseP * Math.PI) * 0.3;
        }

        // After resolve (progress > 0.65), particles slowly fade
        if (progress > 0.7) {
          const fadeP = Math.min((progress - 0.7) / 0.2, 1);
          p.alpha *= (1 - fadeP * 0.6);
        }

        if (p.alpha < 0.005) continue;

        // Draw
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        if (p.layer === 3) {
          ctx.fillStyle = `hsla(${p.hue}, 80%, 70%, ${p.alpha})`;
        } else if (p.layer === 2) {
          ctx.fillStyle = `rgba(200, 220, 240, ${p.alpha})`;
        } else {
          ctx.fillStyle = `rgba(120, 130, 160, ${p.alpha})`;
        }
        ctx.fill();

        // Layer-3 particles get a subtle glow
        if (p.layer === 3 && p.alpha > 0.15) {
          const glowGrad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 4);
          glowGrad.addColorStop(0, `hsla(${p.hue}, 80%, 70%, ${p.alpha * 0.3})`);
          glowGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = glowGrad;
          ctx.fillRect(p.x - p.radius * 4, p.y - p.radius * 4, p.radius * 8, p.radius * 8);
        }
      }

      // ════════════════════════════════════
      // PHASE 6: KnowUrDB wordmark focus-resolve (48% → 72%)
      // From blurred/ghostly → crisp sharp text
      // ════════════════════════════════════
      const wordP = progress < 0.48 ? 0 : Math.min((progress - 0.48) / 0.24, 1);
      if (wordP > 0) {
        const wordEased = easeOutQuint(wordP);
        const isMobile = w < 768;
        const fontSize = isMobile ? 36 : w < 1024 ? 50 : 70;
        const wordText = 'KnowUrDB';

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = `700 ${fontSize}px Inter, -apple-system, sans-serif`;

        const textWidth = measureText(wordText, fontSize, '700');

        // Ghost layer (pre-resolve) — subtle, unfocused
        if (wordEased < 1) {
          const ghostAlpha = (1 - wordEased) * 0.08;
          ctx.filter = `blur(${(1 - wordEased) * 12}px)`;
          ctx.fillStyle = `rgba(34, 211, 238, ${ghostAlpha})`;
          ctx.fillText(wordText, cx, cy - 10);
          ctx.filter = 'none';
        }

        // Main text — resolving from blurry to crisp
        const textAlpha = easeOutCubic(wordEased);
        const blurAmount = (1 - wordEased) * 6;

        if (blurAmount > 0.3) {
          ctx.filter = `blur(${blurAmount}px)`;
        } else {
          ctx.filter = 'none';
        }

        // Text color: starts as cyan-tinted, resolves to cool white
        const cyanInfluence = Math.max(0, 1 - wordEased * 1.5);
        const r = Math.round(244 - cyanInfluence * 210);
        const g = Math.round(244 - cyanInfluence * 33);
        const b = Math.round(245 - cyanInfluence * 7);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${textAlpha})`;
        ctx.fillText(wordText, cx, cy - 10);
        ctx.filter = 'none';

        // Subtle aqua edge illumination during resolve peak
        if (wordEased > 0.3 && wordEased < 0.85) {
          const edgeP = Math.sin((wordEased - 0.3) / 0.55 * Math.PI);
          ctx.strokeStyle = `rgba(34, 211, 238, ${edgeP * 0.12})`;
          ctx.lineWidth = 0.6;
          ctx.strokeText(wordText, cx, cy - 10);
        }

        // Soft aqua glow behind wordmark during focus
        if (wordEased > 0.2 && wordEased < 0.9) {
          const glowP = Math.sin((wordEased - 0.2) / 0.7 * Math.PI);
          const wordGlow = ctx.createRadialGradient(cx, cy - 10, 0, cx, cy - 10, textWidth * 0.8);
          wordGlow.addColorStop(0, `rgba(34, 211, 238, ${glowP * 0.1})`);
          wordGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = wordGlow;
          ctx.fillRect(0, 0, w, h);
        }

        ctx.restore();
      }

      // ════════════════════════════════════
      // PHASE 7: Subtitle resolve (62% → 80%)
      // ════════════════════════════════════
      const subP = progress < 0.62 ? 0 : Math.min((progress - 0.62) / 0.18, 1);
      if (subP > 0) {
        const subEased = easeOutCubic(subP);
        const isMobile = w < 768;
        const subSize = isMobile ? 12 : 14;
        const subText = 'Turn questions into clarity.';

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = `500 ${subSize}px Inter, -apple-system, sans-serif`;

        const subBlur = (1 - subEased) * 4;
        const subY = cy + (isMobile ? 30 : 42) + (1 - subEased) * 8;

        if (subBlur > 0.3) {
          ctx.filter = `blur(${subBlur}px)`;
        }

        // Starts slightly cyan, resolves to zinc-300
        const subCyan = Math.max(0, 1 - subEased * 2);
        const sr = Math.round(212 - subCyan * 178);
        const sg = Math.round(212 - subCyan * 1);
        const sb = 216;
        ctx.fillStyle = `rgba(${sr}, ${sg}, ${sb}, ${easeOutCubic(subEased)})`;
        ctx.fillText(subText, cx, subY);
        ctx.filter = 'none';

        // Tiny aqua light pass across subtitle
        if (subEased > 0.4 && subEased < 0.9) {
          const passP = (subEased - 0.4) / 0.5;
          const passX = cx - 120 + passP * 240;
          const passGrad = ctx.createRadialGradient(passX, subY, 0, passX, subY, 40);
          passGrad.addColorStop(0, `rgba(34, 211, 238, ${Math.sin(passP * Math.PI) * 0.08})`);
          passGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = passGrad;
          ctx.fillRect(passX - 40, subY - 20, 80, 40);
        }

        ctx.restore();
      }

      // ════════════════════════════════════
      // PHASE 8: Signal progress filament (20% → 85%)
      // A thin intelligence path that tracks system readiness
      // ════════════════════════════════════
      const railStartP = progress < 0.2 ? 0 : Math.min((progress - 0.2) / 0.05, 1);
      const railProgress = progress < 0.2 ? 0 : Math.min((progress - 0.2) / 0.65, 1);
      const railEased = easeInOutCubic(railProgress);

      if (railStartP > 0) {
        const isMobile = w < 768;
        const railWidth = isMobile ? 200 : 280;
        const railX = cx - railWidth / 2;
        const railY = cy + (isMobile ? 58 : 78);
        const railAppear = easeOutCubic(railStartP);

        // After wordmark is settled, dim the rail
        const railFade = progress > 0.85 ? Math.max(0, 1 - (progress - 0.85) / 0.1) : 1;
        const railAlpha = railAppear * railFade;

        // Inactive filament base
        ctx.beginPath();
        ctx.moveTo(railX, railY);
        ctx.lineTo(railX + railWidth, railY);
        ctx.strokeStyle = `rgba(255, 255, 255, ${0.06 * railAlpha})`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Active portion
        const activeEnd = railX + railWidth * railEased;
        if (railEased > 0) {
          ctx.beginPath();
          ctx.moveTo(railX, railY);
          ctx.lineTo(activeEnd, railY);
          ctx.strokeStyle = `rgba(34, 211, 238, ${0.5 * railAlpha})`;
          ctx.lineWidth = 1.2;
          ctx.stroke();

          // Signal head — bright point
          const headGlow = ctx.createRadialGradient(activeEnd, railY, 0, activeEnd, railY, 8);
          headGlow.addColorStop(0, `rgba(255, 255, 255, ${0.7 * railAlpha})`);
          headGlow.addColorStop(0.3, `rgba(34, 211, 238, ${0.4 * railAlpha})`);
          headGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = headGlow;
          ctx.fillRect(activeEnd - 8, railY - 8, 16, 16);

          // Small energy wake behind the head
          const wakeLen = Math.min(railEased * railWidth, 30);
          const wakeGrad = ctx.createLinearGradient(activeEnd - wakeLen, railY, activeEnd, railY);
          wakeGrad.addColorStop(0, 'rgba(34, 211, 238, 0)');
          wakeGrad.addColorStop(1, `rgba(34, 211, 238, ${0.2 * railAlpha})`);
          ctx.beginPath();
          ctx.moveTo(activeEnd - wakeLen, railY);
          ctx.lineTo(activeEnd, railY);
          ctx.strokeStyle = wakeGrad;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }

      // ════════════════════════════════════
      // PHASE 9: Global exit fade
      // ════════════════════════════════════
      if (progress >= 0.92) {
        const exitP = (progress - 0.92) / 0.08;
        ctx.fillStyle = `rgba(2, 2, 4, ${easeInOutCubic(exitP) * 0.4})`;
        ctx.fillRect(0, 0, w, h);
      }

      // ─── Continue or exit ───
      if (progress < 1) {
        rAF = requestAnimationFrame(animate);
      } else {
        triggerExit();
      }
    };

    // ─── Reduced motion: skip cinematic, just show brand briefly ───
    const animateReduced = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / 1200, 1); // 1.2s for reduced motion
      const w = window.innerWidth;

      ctx.clearRect(0, 0, w, window.innerHeight);

      const alpha = progress < 0.5 ? easeOutCubic(progress / 0.5) : 1;
      const isMobile = w < 768;
      const fontSize = isMobile ? 36 : w < 1024 ? 50 : 70;

      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.font = `700 ${fontSize}px Inter, -apple-system, sans-serif`;
      ctx.fillStyle = `rgba(244, 244, 245, ${alpha})`;
      ctx.fillText('KnowUrDB', cx, cy - 10);

      ctx.font = `500 ${isMobile ? 12 : 14}px Inter, -apple-system, sans-serif`;
      ctx.fillStyle = `rgba(212, 212, 216, ${alpha * 0.8})`;
      ctx.fillText('Turn questions into clarity.', cx, cy + (isMobile ? 30 : 42));
      ctx.restore();

      if (progress < 1) {
        rAF = requestAnimationFrame(animateReduced);
      } else {
        triggerExit();
      }
    };

    window.addEventListener('resize', resize);
    resize();
    rAF = requestAnimationFrame(prefersReducedMotion ? animateReduced : animate);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(rAF);
    };
  }, [prefersReducedMotion, triggerExit]);

  return (
    <div
      className={`fixed inset-0 z-[9999] h-[100dvh] w-full bg-[#020204] overflow-hidden select-none touch-none pointer-events-auto transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)] ${isExit ? 'opacity-0 scale-[1.02]' : 'opacity-100 scale-100'}`}
    >
      {/* Grain texture overlay */}
      <div className="absolute inset-0 bg-noise z-0"></div>

      {/* The single cinematic canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 z-10"
      />
    </div>
  );
};
