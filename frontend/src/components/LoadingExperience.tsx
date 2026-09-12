import React, { useEffect, useRef, useState } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

const STAGES = [
  "Preparing workspace",
  "Loading database intelligence",
  "Almost ready"
];

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [phase, setPhase] = useState<'darkness' | 'data-signal' | 'brand-energy' | 'letter-reveal' | 'focus' | 'exit'>('darkness');
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Handle prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Viewport & Scroll Locking
  useEffect(() => {
    const originalBodyOverflow = document.body.style.overflow;
    const originalHtmlOverflow = document.documentElement.style.overflow;
    
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalBodyOverflow;
      document.documentElement.style.overflow = originalHtmlOverflow;
    };
  }, []);

  // Cinematic Timeline
  useEffect(() => {
    // 0.0s - Darkness (initial state)
    
    // 0.3s - Atmosphere begins
    // 0.5s - Data signals appear
    const p1 = setTimeout(() => setPhase('data-signal'), 500);
    
    // 0.7s - Brand reveal begins
    const p2 = setTimeout(() => setPhase('brand-energy'), 700);

    // 1.1s - KnowUrDB becomes readable
    const p3 = setTimeout(() => setPhase('letter-reveal'), 1100);

    // 1.6s - Focus / Category / Product Statement appears
    const p4 = setTimeout(() => setPhase('focus'), 1600);

    // 2.8s - Begin exit transition
    const p5 = setTimeout(() => {
      setPhase('exit');
      
      // Wait for exit transition to show underlying app
      setTimeout(() => {
        onReveal();
      }, 500);

      // Unmount completely
      setTimeout(() => {
        onComplete();
      }, 1000);
    }, 2800);

    return () => {
      clearTimeout(p1);
      clearTimeout(p2);
      clearTimeout(p3);
      clearTimeout(p4);
      clearTimeout(p5);
    };
  }, [onReveal, onComplete]);

  // Status Message Cycling
  useEffect(() => {
    if (phase !== 'focus') return;
    
    const intervalTime = 600; // Fast cycling for status messages
    let currentStage = 0;
    
    const interval = setInterval(() => {
      currentStage++;
      if (currentStage < STAGES.length) {
        setStageIndex(currentStage);
      } else {
        clearInterval(interval);
      }
    }, intervalTime);

    return () => clearInterval(interval);
  }, [phase]);

  // Canvas background metaphor (Intelligent Schema / Data Nodes)
  useEffect(() => {
    if (prefersReducedMotion) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: { x: number, y: number, vx: number, vy: number, radius: number }[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initParticles();
    };

    const initParticles = () => {
      particles = [];
      const numParticles = Math.floor((canvas.width * canvas.height) / 25000); // Sparse
      for (let i = 0; i < Math.min(numParticles, 60); i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.1, // Extremely slow, organic movement
          vy: (Math.random() - 0.5) * 0.1,
          radius: Math.random() * 1.5 + 0.5
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around gently
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();

        // Draw connections for schema effect
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 120) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(34, 211, 238, ${0.04 * (1 - dist / 120)})`; // Very subtle cyan/white
            ctx.lineWidth = 0.5;
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }
      animationFrameId = requestAnimationFrame(draw);
    };

    window.addEventListener('resize', resize);
    resize();
    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [prefersReducedMotion]);

  // Derived states for cinematic transition
  const showAtmosphere = phase !== 'darkness' && phase !== 'exit';
  const showData = (phase === 'data-signal' || phase === 'brand-energy' || phase === 'letter-reveal' || phase === 'focus');
  const showBrand = (phase === 'brand-energy' || phase === 'letter-reveal' || phase === 'focus');
  const showLightSweep = phase === 'letter-reveal' || phase === 'focus'; // Starts after letters appear
  const showDetails = phase === 'focus';
  const isExiting = phase === 'exit';

  return (
    <div 
      className={`fixed inset-0 z-[9999] h-[100dvh] w-screen flex items-center justify-center bg-[#050507] text-zinc-100 overflow-hidden select-none touch-none pointer-events-auto transition-all duration-1000 ease-in-out ${isExiting ? 'opacity-0 scale-[1.02] filter blur-[4px]' : 'opacity-100'}`}
    >
      {/* Central expanding light on exit */}
      <div className={`absolute inset-0 pointer-events-none transition-all duration-700 ${isExiting ? 'bg-zinc-100/5 z-50' : 'bg-transparent'}`}></div>

      {/* Subtle radial glows (Atmosphere) */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${showAtmosphere ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-violet-900/10 blur-[120px] animate-pulse-slow"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-cyan-900/5 blur-[80px]"></div>
      </div>

      {/* Canvas Background Metaphor */}
      <canvas 
        ref={canvasRef} 
        className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${showData ? 'opacity-50' : 'opacity-0'}`}
        style={{ maskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)', WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)' }}
      />

      {/* Micro details (Edge UI) */}
      <div className={`absolute top-6 left-6 md:top-8 md:left-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-1000 hidden sm:block ${showDetails ? 'opacity-100' : 'opacity-0'}`}>
        KNOWURDB <br/> INTELLIGENCE SYSTEM
      </div>
      <div className={`absolute bottom-6 left-6 md:bottom-8 md:left-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-1000 hidden sm:block ${showDetails ? 'opacity-100' : 'opacity-0'}`}>
        NATURAL LANGUAGE → DATABASE
      </div>
      <div className={`absolute bottom-6 right-6 md:bottom-8 md:right-8 text-[10px] font-mono tracking-widest text-cyan-900/50 transition-opacity duration-1000 hidden sm:block ${showDetails ? 'opacity-100 animate-pulse-slow' : 'opacity-0'}`}>
        INITIALIZING
      </div>

      {/* Central Content */}
      <div className="relative z-10 flex flex-col items-center justify-center -mt-8 md:-mt-16 w-full max-w-2xl px-4">
        
        {/* Brand Reveal */}
        <div className={`relative mb-4 md:mb-6 transition-all duration-700 ${showBrand ? 'opacity-100' : 'opacity-0'}`}>
          {showBrand && (
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-zinc-100 relative animate-brand-reveal-premium">
              knowUrDB
              {/* One-time elegant light sweep */}
              {showLightSweep && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-100/40 to-transparent mix-blend-overlay animate-light-sweep-single pointer-events-none"></div>
              )}
            </h1>
          )}
        </div>

        {/* Subtitle / Product Statement */}
        <div className={`flex flex-col items-center transition-all duration-1000 ${showDetails ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <div className="text-[10px] md:text-xs font-bold tracking-[0.25em] text-cyan-500/80 uppercase mb-3">
            Database Intelligence Platform
          </div>
          <p className="text-sm md:text-base font-medium tracking-wide text-zinc-400 mb-12 text-center">
            Understand your data. Ask it anything.
          </p>

          {/* Custom minimal line indicator */}
          <div className="w-full max-w-[200px] flex flex-col items-center">
            <div className="w-full h-[1px] bg-zinc-800/80 relative overflow-hidden mb-4">
              <div className="absolute top-0 left-0 h-full w-[40px] bg-cyan-400/80 shadow-[0_0_8px_rgba(34,211,238,0.8)] rounded-full animate-orbit-dot"></div>
            </div>

            {/* Status Messages */}
            <div className="h-4 flex items-center justify-center relative w-full overflow-hidden">
              {STAGES.map((msg, idx) => (
                <span 
                  key={idx}
                  className={`absolute text-[10px] font-medium tracking-widest text-zinc-500 transition-all duration-500 ease-out
                    ${idx === stageIndex ? 'opacity-100 transform-none' : 
                      idx < stageIndex ? 'opacity-0 -translate-y-2' : 'opacity-0 translate-y-2'}`}
                >
                  {msg}
                </span>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
