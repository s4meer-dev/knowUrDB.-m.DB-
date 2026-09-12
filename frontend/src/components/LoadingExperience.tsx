import React, { useEffect, useRef, useState } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

const STAGES = [
  "INITIALIZING WORKSPACE",
  "LOADING DATA INTELLIGENCE",
  "PREPARING ENVIRONMENT",
  "READY"
];

type Phase = 
  | 'darkness' 
  | 'signal-field' 
  | 'wordmark-energy' 
  | 'wordmark-resolves' 
  | 'light-sweep' 
  | 'category-popup' 
  | 'tagline-materialize' 
  | 'loading-rail'
  | 'exit';

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>('darkness');
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [glitchActive, setGlitchActive] = useState(false);

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
    
    // 0.3s - Signal field
    const p1 = setTimeout(() => setPhase('signal-field'), 300);
    
    // 0.6s - Wordmark energy (starts mask reveal)
    const p2 = setTimeout(() => setPhase('wordmark-energy'), 600);

    // 1.1s - Wordmark resolves (trigger glitch)
    const p3 = setTimeout(() => {
      setPhase('wordmark-resolves');
      if (!prefersReducedMotion) {
        setGlitchActive(true);
        setTimeout(() => setGlitchActive(false), 50); // 50ms glitch
      }
    }, 1100);

    // 1.3s - Light sweep
    const p4 = setTimeout(() => setPhase('light-sweep'), 1300);

    // 1.5s - Category popup
    const p5 = setTimeout(() => setPhase('category-popup'), 1500);

    // 1.7s - Tagline materialize
    const p6 = setTimeout(() => setPhase('tagline-materialize'), 1700);

    // 2.0s - Loading rail
    const p7 = setTimeout(() => setPhase('loading-rail'), 2000);

    // 3.0s - Begin exit transition
    const p8 = setTimeout(() => {
      setPhase('exit');
      
      // 3.5s - Wait for exit transition to show underlying app
      setTimeout(() => {
        onReveal();
      }, 500);

      // 4.0s - Unmount completely
      setTimeout(() => {
        onComplete();
      }, 1000);
    }, 3000);

    return () => {
      clearTimeout(p1); clearTimeout(p2); clearTimeout(p3);
      clearTimeout(p4); clearTimeout(p5); clearTimeout(p6);
      clearTimeout(p7); clearTimeout(p8);
    };
  }, [onReveal, onComplete, prefersReducedMotion]);

  // Status Message Cycling
  useEffect(() => {
    if (phase !== 'loading-rail') return;
    
    const intervalTime = 250; // Fast cycling for status messages to reach READY before exit
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
    let particles: { x: number, y: number, vx: number, vy: number, radius: number, isCore: boolean }[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initParticles();
    };

    const initParticles = () => {
      particles = [];
      const numParticles = Math.floor((canvas.width * canvas.height) / 25000); // Sparse
      for (let i = 0; i < Math.min(numParticles, 50); i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.15,
          vy: (Math.random() - 0.5) * 0.15,
          radius: Math.random() * 1.5 + 0.5,
          isCore: Math.random() > 0.8
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.width / 2;
      const centerY = (canvas.height / 2) - 40; // Offset for wordmark
      
      // Determine if we should converge
      const shouldConverge = phase !== 'darkness' && phase !== 'exit';

      ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        
        if (shouldConverge && p.isCore) {
          // Slowly move towards center
          const dx = centerX - p.x;
          const dy = centerY - p.y;
          p.x += dx * 0.001;
          p.y += dy * 0.001;
        } else {
          p.x += p.vx;
          p.y += p.vy;
        }

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
            ctx.strokeStyle = `rgba(34, 211, 238, ${0.05 * (1 - dist / 120)})`; // Very subtle cyan/white
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
  }, [prefersReducedMotion, phase]);

  // Derived states for cinematic transition
  const showAtmosphere = phase !== 'darkness' && phase !== 'exit';
  const showData = phase !== 'darkness';
  const isExiting = phase === 'exit';

  // State checks for elements
  const hasWordmarkStarted = phase !== 'darkness' && phase !== 'signal-field';
  const hasWordmarkResolved = hasWordmarkStarted && phase !== 'wordmark-energy';
  const hasLightSweepStarted = phase === 'light-sweep' || phase === 'category-popup' || phase === 'tagline-materialize' || phase === 'loading-rail';
  const hasCategoryStarted = phase === 'category-popup' || phase === 'tagline-materialize' || phase === 'loading-rail';
  const hasTaglineStarted = phase === 'tagline-materialize' || phase === 'loading-rail';
  const hasRailStarted = phase === 'loading-rail';

  // We only want the light sweep to run once when triggered
  const showLightSweep = hasLightSweepStarted && !isExiting;

  return (
    <div 
      className={`fixed inset-0 z-[9999] h-[100dvh] w-screen flex items-center justify-center bg-[#050507] text-zinc-100 overflow-hidden select-none touch-none pointer-events-auto transition-all duration-700 ease-in-out ${isExiting ? 'opacity-0' : 'opacity-100'}`}
    >
      {/* Central expanding light on exit */}
      <div className={`absolute inset-0 pointer-events-none transition-all duration-700 ${isExiting ? 'bg-zinc-100/5 z-50' : 'bg-transparent'}`}></div>

      {/* Subtle radial glows (Atmosphere) */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${showAtmosphere ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-violet-900/10 blur-[120px] animate-breathe"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-cyan-900/5 blur-[80px]"></div>
      </div>

      {/* Center Elliptical Light (Behind Wordmark) */}
      <div className={`absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] md:w-[500px] h-[150px] rounded-[100%] bg-cyan-400/5 blur-[50px] transition-all duration-1000 pointer-events-none ${hasWordmarkStarted ? 'opacity-100 scale-100' : 'opacity-0 scale-75'}`}></div>

      {/* Canvas Background Metaphor */}
      <canvas 
        ref={canvasRef} 
        className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${showData ? 'opacity-60' : 'opacity-0'}`}
        style={{ maskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)', WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 80%)' }}
      />

      {/* Micro details (Edge UI) */}
      <div className={`absolute top-6 left-6 md:top-8 md:left-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-1000 hidden sm:block ${hasRailStarted ? 'opacity-40' : 'opacity-0'}`}>
        KNOWURDB <br/> INTELLIGENCE SYSTEM
      </div>
      <div className={`absolute bottom-6 left-6 md:bottom-8 md:left-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-1000 hidden sm:block ${hasRailStarted ? 'opacity-40' : 'opacity-0'}`}>
        NATURAL LANGUAGE → DATABASE
      </div>
      <div className={`absolute bottom-6 right-6 md:bottom-8 md:right-8 text-[10px] font-mono tracking-widest text-cyan-900/50 transition-opacity duration-1000 hidden sm:block ${hasRailStarted ? 'opacity-100 animate-pulse-slow' : 'opacity-0'}`}>
        INITIALIZING
      </div>

      {/* Central Content */}
      <div className="relative z-10 flex flex-col items-center justify-center -mt-8 md:-mt-16 w-full max-w-2xl px-4">
        
        {/* Brand Reveal */}
        <div className={`relative mb-6 md:mb-8 transition-opacity duration-300`}>
          {hasWordmarkStarted && (
            <h1 
              className={`text-[40px] md:text-[64px] lg:text-[96px] font-bold tracking-tight text-white relative ${glitchActive ? 'animate-glitch-micro' : ''}`}
              style={{
                maskImage: hasWordmarkResolved ? 'none' : 'linear-gradient(-90deg, transparent 50%, black 50%)',
                WebkitMaskImage: hasWordmarkResolved ? 'none' : 'linear-gradient(-90deg, transparent 50%, black 50%)',
                maskSize: '200% 100%',
                WebkitMaskSize: '200% 100%',
                animation: hasWordmarkResolved ? 'none' : 'maskReveal 0.5s ease-out forwards'
              }}
            >
              <span className={hasWordmarkResolved ? '' : 'animate-text-glow-pulse'}>
                KnowUrDB
              </span>
              
              {/* One-time elegant light sweep */}
              {showLightSweep && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-100/60 to-transparent mix-blend-overlay animate-light-sweep-single pointer-events-none"></div>
              )}
            </h1>
          )}
        </div>

        {/* Subtitle / Product Statement */}
        <div className={`flex flex-col items-center`}>
          {hasCategoryStarted && (
            <div className="text-[10px] md:text-xs font-bold tracking-[0.25em] text-cyan-500/80 uppercase mb-3 animate-pop-up-blur opacity-0" style={{ animationDelay: '0ms', animationFillMode: 'forwards' }}>
              Database Intelligence Platform
            </div>
          )}
          
          {hasTaglineStarted && (
            <p className="text-sm md:text-base font-medium tracking-wide text-zinc-400 mb-14 text-center animate-materialize opacity-0" style={{ animationDelay: '0ms', animationFillMode: 'forwards' }}>
              Understand your data. Ask it anything.
            </p>
          )}

          {/* Custom multi-layer data rail */}
          {hasRailStarted && (
            <div className="w-full max-w-[240px] flex flex-col items-center opacity-0 animate-fade-in" style={{ animationFillMode: 'forwards' }}>
              <div className="w-full relative h-[2px] mb-6">
                {/* Layer 1: Base Line */}
                <div className="absolute inset-0 bg-zinc-800/80 rounded-full"></div>
                
                {/* Layer 2: Progress Line */}
                <div className="absolute top-0 left-0 h-full bg-cyan-900/60 rounded-full origin-left animate-rail-progress"></div>
                
                {/* Layer 3 & 5: Moving point & Glow */}
                <div className="absolute top-1/2 -translate-y-1/2 w-4 h-[2px] bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)] rounded-full animate-rail-point origin-center">
                  {/* Layer 6: Pulse */}
                  <div className="absolute inset-0 bg-white rounded-full animate-rail-glow"></div>
                </div>
              </div>

              {/* Status Messages */}
              <div className="h-4 flex items-center justify-center relative w-full overflow-hidden">
                {STAGES.map((msg, idx) => (
                  <span 
                    key={idx}
                    className={`absolute text-[9px] md:text-[10px] font-medium tracking-widest text-zinc-500 transition-all duration-300 ease-out uppercase
                      ${idx === stageIndex ? 'opacity-100 transform-none' : 
                        idx < stageIndex ? 'opacity-0 -translate-y-4' : 'opacity-0 translate-y-4'}`}
                  >
                    {msg}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
