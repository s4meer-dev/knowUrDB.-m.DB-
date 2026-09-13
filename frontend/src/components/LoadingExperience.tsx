import React, { useEffect, useRef, useState } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

const STAGES = [
  "PREPARING YOUR INTELLIGENCE ENVIRONMENT",
  "INITIALIZING WORKSPACE",
  "ALMOST READY",
  "READY"
];

type Phase = 
  | 'void' 
  | 'stars' 
  | 'atmosphere' 
  | 'particles' 
  | 'signal' 
  | 'energy' 
  | 'brand_form' 
  | 'brand_lock' 
  | 'light_sweep' 
  | 'category' 
  | 'tagline' 
  | 'rail' 
  | 'status' 
  | 'stabilize' 
  | 'ready' 
  | 'exit';

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>('void');
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Handle prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Viewport & Scroll Locking - STRICT
  useEffect(() => {
    document.documentElement.classList.add('lock-scroll');
    document.body.classList.add('lock-scroll');
    // Lock scroll position
    const top = window.scrollY;
    
    const handleScroll = (e: Event) => {
      e.preventDefault();
      window.scrollTo(0, top);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: false });
    window.addEventListener('wheel', handleScroll, { passive: false });
    window.addEventListener('touchmove', handleScroll, { passive: false });

    return () => {
      document.documentElement.classList.remove('lock-scroll');
      document.body.classList.remove('lock-scroll');
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('wheel', handleScroll);
      window.removeEventListener('touchmove', handleScroll);
    };
  }, []);

  // Cinematic Timeline Master Sequence
  useEffect(() => {
    const timeline = [
      { t: 200, p: 'stars' as Phase },
      { t: 400, p: 'atmosphere' as Phase },
      { t: 600, p: 'particles' as Phase },
      { t: 800, p: 'signal' as Phase },
      { t: 1000, p: 'energy' as Phase },
      { t: 1100, p: 'brand_form' as Phase },
      { t: 1850, p: 'brand_lock' as Phase },
      { t: 2000, p: 'light_sweep' as Phase },
      { t: 2150, p: 'category' as Phase },
      { t: 2350, p: 'tagline' as Phase },
      { t: 2550, p: 'rail' as Phase },
      { t: 2700, p: 'status' as Phase },
      { t: 3000, p: 'stabilize' as Phase },
      { t: 3100, p: 'ready' as Phase },
      { t: 3200, p: 'exit' as Phase },
    ];

    const timeouts = timeline.map(({ t, p }) => 
      setTimeout(() => setPhase(p), t)
    );

    // Coordinate Reveal & Unmount
    const revealTimeout = setTimeout(() => {
      onReveal(); // Reveal underlying app while exit transition is happening
    }, 3700);

    const unmountTimeout = setTimeout(() => {
      onComplete(); // Remove loading component
    }, 4000);

    return () => {
      timeouts.forEach(clearTimeout);
      clearTimeout(revealTimeout);
      clearTimeout(unmountTimeout);
    };
  }, [onReveal, onComplete]);

  // Status Message Master Timeline Sync
  useEffect(() => {
    if (phase === 'status') setStageIndex(0);
    else if (phase === 'stabilize') setStageIndex(1);
    else if (phase === 'ready') setStageIndex(3);
  }, [phase]);

  // Canvas background metaphor (Intelligent Schema / Data Nodes)
  useEffect(() => {
    if (prefersReducedMotion) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    // Layer 1: Distant Stars
    // Layer 2: Brighter Stars
    // Layer 3: Data Nodes
    let stars: { x: number, y: number, r: number, alpha: number, layer: number }[] = [];
    let nodes: { x: number, y: number, vx: number, vy: number, r: number, isCore: boolean }[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initElements();
    };

    const initElements = () => {
      stars = [];
      nodes = [];
      
      const isMobile = window.innerWidth < 768;
      const starCount = isMobile ? 80 : 200;
      const nodeCount = isMobile ? 25 : 60;
      
      // Init Stars
      for (let i = 0; i < starCount; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: Math.random() * 0.8 + 0.2,
          alpha: Math.random() * 0.5 + 0.1,
          layer: Math.random() > 0.8 ? 2 : 1
        });
      }
      
      // Init Nodes
      for (let i = 0; i < nodeCount; i++) {
        nodes.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.1,
          vy: (Math.random() - 0.5) * 0.1,
          r: Math.random() * 1.2 + 0.5,
          isCore: Math.random() > 0.7
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.width / 2;
      const centerY = (canvas.height / 2) - 60; // Offset for wordmark
      
      const pIdx = ['void', 'stars', 'atmosphere', 'particles', 'signal', 'energy', 'brand_form', 'brand_lock', 'light_sweep', 'category', 'tagline', 'rail', 'status', 'stabilize', 'ready', 'exit'].indexOf(phase);
      
      const showStars = pIdx >= 1;
      const showNodes = pIdx >= 3;
      const shouldConverge = pIdx >= 4 && pIdx < 13; // Converge from 'signal' to 'stabilize'
      const isExit = pIdx >= 15;

      if (isExit) {
        ctx.globalAlpha -= 0.02;
        if (ctx.globalAlpha < 0) ctx.globalAlpha = 0;
      }

      // Draw Stars
      if (showStars) {
        for (const s of stars) {
          ctx.beginPath();
          ctx.fillStyle = `rgba(255, 255, 255, ${s.alpha * (s.layer === 2 ? 1.5 : 1)})`;
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fill();
          
          // Gentle twinkle/drift for layer 2
          if (s.layer === 2) {
             s.y -= 0.05;
             if (s.y < 0) s.y = canvas.height;
             s.alpha = s.alpha + (Math.sin(Date.now() / 1000 + s.x) * 0.005);
          }
        }
      }

      // Draw Data Universe
      if (showNodes) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
        for (let i = 0; i < nodes.length; i++) {
          const p = nodes[i];
          
          if (shouldConverge && p.isCore) {
            const dx = centerX - p.x;
            const dy = centerY - p.y;
            p.x += dx * 0.002;
            p.y += dy * 0.002;
          } else {
            p.x += p.vx;
            p.y += p.vy;
          }

          if (p.x < 0) p.x = canvas.width;
          if (p.x > canvas.width) p.x = 0;
          if (p.y < 0) p.y = canvas.height;
          if (p.y > canvas.height) p.y = 0;

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fill();

          for (let j = i + 1; j < nodes.length; j++) {
            const p2 = nodes[j];
            const dx = p.x - p2.x;
            const dy = p.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 100) {
              ctx.beginPath();
              ctx.strokeStyle = `rgba(34, 211, 238, ${0.03 * (1 - dist / 100)})`;
              ctx.lineWidth = 0.5;
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();
            }
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

  // Derived states
  const pIdx = ['void', 'stars', 'atmosphere', 'particles', 'signal', 'energy', 'brand_form', 'brand_lock', 'light_sweep', 'category', 'tagline', 'rail', 'status', 'stabilize', 'ready', 'exit'].indexOf(phase);
  
  const showAtmosphere = pIdx >= 2;
  const showEnergy = pIdx >= 5;
  const showBrandForm = pIdx >= 6;
  const showBrandLock = pIdx >= 7;
  const showLightSweep = pIdx >= 8 && pIdx < 15;
  const showCategory = pIdx >= 9;
  const showTagline = pIdx >= 10;
  const showRail = pIdx >= 11;
  const showStatus = pIdx >= 12;
  const isExit = pIdx >= 15;

  return (
    <div 
      className={`fixed inset-0 z-[9999] h-[100dvh] w-full flex items-center justify-center bg-[#050507] text-zinc-100 overflow-hidden select-none touch-none pointer-events-auto transition-all duration-700 ease-in-out ${isExit ? 'opacity-0 scale-[1.02]' : 'opacity-100 scale-100'}`}
    >
      {/* Central Expanding Exit Light */}
      <div className={`absolute inset-0 pointer-events-none transition-all duration-700 ${isExit ? 'bg-cyan-950/10 z-50' : 'bg-transparent'}`}></div>

      {/* Atmospheric Nebula */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-1000 ${showAtmosphere ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-violet-900/10 blur-[100px] animate-cinematic-breathe"></div>
      </div>

      {/* Central Energy Field */}
      <div className={`absolute top-[40%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[200px] h-[100px] rounded-full bg-cyan-500/10 blur-[60px] transition-all duration-700 pointer-events-none ${showEnergy ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`}></div>

      {/* Universe Canvas */}
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 pointer-events-none opacity-80"
      />

      {/* Central Content Container */}
      <div className="relative z-10 flex flex-col items-center justify-center -mt-16 w-full max-w-2xl px-4">
        
        {/* KnowUrDB Wordmark */}
        <div className="relative mb-6 flex justify-center items-center h-20">
          {showBrandForm && (
            <h1 
              className="text-[34px] md:text-[56px] lg:text-[78px] font-bold tracking-tight relative"
            >
              {/* Internal Edge Energy / Formation Layer */}
              <span 
                className={`absolute inset-0 animate-wordmark-edge ${showBrandLock ? 'hidden' : ''}`}
              >
                KnowUrDB
              </span>
              
              {/* Base Wordmark */}
              <span 
                className="animate-wordmark-base text-zinc-100 mix-blend-plus-lighter"
                style={{
                  clipPath: showBrandLock ? 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' : 'polygon(0 0, 0 0, 0 100%, 0 100%)',
                  transition: 'clip-path 0.75s cubic-bezier(0.2, 0.8, 0.2, 1)'
                }}
              >
                KnowUrDB
              </span>

              {/* Light Sweep */}
              {showLightSweep && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-100/40 to-transparent mix-blend-overlay animate-light-sweep pointer-events-none"></div>
              )}
            </h1>
          )}
        </div>

        {/* Text Container */}
        <div className="flex flex-col items-center min-h-[80px]">
          {showCategory && (
            <div className="text-[9px] md:text-[10px] font-bold tracking-[0.3em] text-cyan-500/80 uppercase mb-4 animate-text-reveal opacity-0">
              Database Intelligence Platform
            </div>
          )}
          
          {showTagline && (
            <p className="text-xs md:text-sm font-medium tracking-widest text-zinc-400 animate-text-reveal opacity-0" style={{ animationDelay: '100ms' }}>
              Understand your data. Ask it anything.
            </p>
          )}
        </div>

        {/* Loading Rail */}
        <div className="mt-12 w-full max-w-[200px] flex flex-col items-center relative min-h-[40px]">
          {showRail && (
            <div className="w-full relative h-[1px] mb-6 opacity-0 animate-rail-line">
              {/* Base Line */}
              <div className="absolute inset-0 bg-zinc-800/80"></div>
              
              {/* Progress */}
              <div className="absolute top-0 left-0 h-full bg-cyan-800/60 origin-left animate-rail-progress"></div>
              
              {/* Energy Point */}
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-[1px] bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)] animate-rail-point origin-center">
                {/* Glow Pulse */}
                <div className="absolute inset-0 bg-white animate-rail-glow"></div>
              </div>
            </div>
          )}

          {/* Status Message */}
          <div className="h-4 flex items-center justify-center relative w-full overflow-hidden">
            {showStatus && STAGES.map((msg, idx) => (
              <span 
                key={idx}
                className={`absolute text-[8px] md:text-[9px] font-medium tracking-[0.2em] text-zinc-500 transition-all duration-300 ease-out uppercase
                  ${idx === stageIndex ? 'opacity-100 transform-none' : 
                    idx < stageIndex ? 'opacity-0 -translate-y-4' : 'opacity-0 translate-y-4'}`}
              >
                {msg}
              </span>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

