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
  | 'signals' 
  | 'converge' 
  | 'brand_trace' 
  | 'brand_energy' 
  | 'brand_resolve' 
  | 'brand_sweep' 
  | 'category' 
  | 'tagline' 
  | 'rail' 
  | 'ready' 
  | 'exit';

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>('void');
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  
  // Use refs for callbacks so they don't trigger useEffect re-runs
  const onRevealRef = useRef(onReveal);
  const onCompleteRef = useRef(onComplete);

  useEffect(() => {
    onRevealRef.current = onReveal;
    onCompleteRef.current = onComplete;
  }, [onReveal, onComplete]);

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
    // 0.00 - 0.40: BLACK / VOID
    // 0.30 - 0.90: distant stars
    // 0.60 - 1.20: galaxy atmosphere
    // 0.90 - 1.50: data signals
    // 1.20 - 1.70: signals converge
    // 1.50 - 2.40: KnowUrDB letter formation (trace -> energy)
    // 2.40 - 2.80: KnowUrDB resolves
    // 2.80 - 3.20: single light sweep
    // 3.00 - 3.40: category text reveal
    // 3.25 - 3.70: tagline reveal
    // 3.50 - 4.20: data rail activates
    // 4.00 - 4.50: status reaches READY
    // 4.50+ : cinematic exit

    const timeline = [
      { t: 300, p: 'stars' as Phase },
      { t: 600, p: 'atmosphere' as Phase },
      { t: 900, p: 'signals' as Phase },
      { t: 1200, p: 'converge' as Phase },
      { t: 1500, p: 'brand_trace' as Phase },
      { t: 2100, p: 'brand_energy' as Phase },
      { t: 2600, p: 'brand_resolve' as Phase },
      { t: 2900, p: 'brand_sweep' as Phase },
      { t: 3200, p: 'category' as Phase },
      { t: 3450, p: 'tagline' as Phase },
      { t: 3700, p: 'rail' as Phase },
      { t: 4200, p: 'ready' as Phase },
      { t: 4600, p: 'exit' as Phase },
    ];

    const timeouts = timeline.map(({ t, p }) => 
      setTimeout(() => setPhase(p), t)
    );

    // Coordinate Reveal & Unmount via Refs to avoid re-rendering issues
    const revealTimeout = setTimeout(() => {
      onRevealRef.current(); // Reveal underlying app while exit transition is happening
    }, 4800);

    const unmountTimeout = setTimeout(() => {
      onCompleteRef.current(); // Remove loading component completely
    }, 5300);

    return () => {
      timeouts.forEach(clearTimeout);
      clearTimeout(revealTimeout);
      clearTimeout(unmountTimeout);
    };
  }, []); // <-- Empty array: GUARANTEED to run exactly once on mount

  // Status Message Master Timeline Sync
  useEffect(() => {
    if (phase === 'rail') setStageIndex(0);
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
      const starCount = isMobile ? 60 : 150; // Very sparse
      const nodeCount = isMobile ? 15 : 40;  // Very sparse network
      
      // Init Stars - Sharp, small, varying opacity
      for (let i = 0; i < starCount; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: Math.random() * 0.6 + 0.1, // Tiny
          alpha: Math.random() * 0.4 + 0.05,
          layer: Math.random() > 0.85 ? 3 : (Math.random() > 0.5 ? 2 : 1) // Distant, Mid, Focal
        });
      }
      
      // Init Nodes - Data Intelligence Field
      for (let i = 0; i < nodeCount; i++) {
        nodes.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.05, // Extremely slow
          vy: (Math.random() - 0.5) * 0.05,
          r: Math.random() * 0.8 + 0.3,
          isCore: Math.random() > 0.8
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      
      const pIdx = ['void', 'stars', 'atmosphere', 'signals', 'converge', 'brand_trace', 'brand_energy', 'brand_resolve', 'brand_sweep', 'category', 'tagline', 'rail', 'ready', 'exit'].indexOf(phase);
      
      const showStars = pIdx >= 1;
      const showNodes = pIdx >= 3;
      const shouldConverge = pIdx >= 4 && pIdx < 12; 
      const isExit = pIdx >= 13;

      if (isExit) {
        ctx.globalAlpha -= 0.015;
        if (ctx.globalAlpha < 0) ctx.globalAlpha = 0;
      }

      // Draw Stars
      if (showStars) {
        for (const s of stars) {
          ctx.beginPath();
          // Layer 3 (focal) is slightly brighter and tinged with cyan/violet
          if (s.layer === 3) {
            ctx.fillStyle = `rgba(180, 240, 255, ${s.alpha * 1.5})`;
          } else {
            ctx.fillStyle = `rgba(255, 255, 255, ${s.alpha})`;
          }
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fill();
          
          // Gentle movement based on layer
          if (s.layer === 3) {
             s.y -= 0.03;
             if (s.y < 0) s.y = canvas.height;
             s.alpha = s.alpha + (Math.sin(Date.now() / 2000 + s.x) * 0.003); // Twinkle
          } else if (s.layer === 2) {
             s.y -= 0.01;
             if (s.y < 0) s.y = canvas.height;
          }
        }
      }

      // Draw Data Universe (Abstract Network)
      if (showNodes) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        for (let i = 0; i < nodes.length; i++) {
          const p = nodes[i];
          
          if (shouldConverge && p.isCore) {
            const dx = centerX - p.x;
            const dy = centerY - p.y;
            p.x += dx * 0.001; // Slower convergence
            p.y += dy * 0.001;
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

            if (dist < 120) {
              ctx.beginPath();
              // Extremely faint connections
              ctx.strokeStyle = `rgba(167, 139, 250, ${0.015 * (1 - dist / 120)})`; 
              ctx.lineWidth = 0.3;
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

  const pIdx = ['void', 'stars', 'atmosphere', 'signals', 'converge', 'brand_trace', 'brand_energy', 'brand_resolve', 'brand_sweep', 'category', 'tagline', 'rail', 'ready', 'exit'].indexOf(phase);
  
  const showAtmosphere = pIdx >= 2;
  const showBrandTrace = pIdx >= 5;
  const showBrandEnergy = pIdx >= 6;
  const showBrandResolve = pIdx >= 7;
  const showBrandSweep = pIdx >= 8 && pIdx < 13;
  const showCategory = pIdx >= 9;
  const showTagline = pIdx >= 10;
  const showRail = pIdx >= 11;
  const isExit = pIdx >= 13;

  return (
    <div 
      className={`fixed inset-0 z-[9999] h-[100dvh] w-full flex items-center justify-center bg-[#020204] text-zinc-100 overflow-hidden select-none touch-none pointer-events-auto transition-all duration-700 ease-in-out ${isExit ? 'opacity-0 scale-[1.03]' : 'opacity-100 scale-100'}`}
    >
      {/* Central Expanding Exit Light */}
      <div className={`absolute inset-0 pointer-events-none transition-all duration-700 ease-out ${isExit ? 'bg-zinc-900/10 z-50' : 'bg-transparent'}`}></div>

      {/* Atmospheric Nebula - Slow breathing, dark violet/indigo */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-1500 ease-in-out ${showAtmosphere ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[70vw] h-[70vw] max-w-[800px] max-h-[800px] rounded-full bg-[radial-gradient(circle,rgba(46,16,101,0.15)_0%,rgba(17,24,39,0)_70%)] animate-cinematic-breathe mix-blend-screen"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40vw] h-[40vw] max-w-[500px] max-h-[500px] rounded-full bg-[radial-gradient(circle,rgba(8,145,178,0.05)_0%,rgba(17,24,39,0)_60%)] animate-cinematic-breathe mix-blend-screen" style={{ animationDelay: '-4s' }}></div>
      </div>

      {/* Universe Canvas */}
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 pointer-events-none opacity-90 mix-blend-screen"
      />

      {/* Central Content Container */}
      <div className="relative z-10 flex flex-col items-center justify-center w-full max-w-2xl px-4">
        
        {/* KnowUrDB Wordmark Container */}
        <div className="relative mb-6 flex justify-center items-center h-24">
          
          {/* Phase 1: Invisible (Wait) */}
          {/* Phase 2: Signal Trace */}
          <h1 className={`absolute text-[34px] md:text-[56px] lg:text-[72px] font-bold tracking-tight text-transparent transition-opacity duration-1000 ${showBrandTrace && !showBrandResolve ? 'opacity-100' : 'opacity-0'}`} style={{ WebkitTextStroke: '1px rgba(167, 139, 250, 0.4)' }}>
            <span className={`block w-full h-full animate-trace-sweep ${showBrandTrace ? '' : 'hidden'}`}>
              KnowUrDB
            </span>
          </h1>

          {/* Phase 3: Internal Energy */}
          <h1 className={`absolute text-[34px] md:text-[56px] lg:text-[72px] font-bold tracking-tight text-transparent bg-clip-text transition-all duration-700 ${showBrandEnergy && !showBrandResolve ? 'opacity-100 scale-100 blur-[2px]' : 'opacity-0 scale-[0.98] blur-[8px]'}`} style={{ backgroundImage: 'linear-gradient(90deg, rgba(34,211,238,0.2) 0%, rgba(139,92,246,0.6) 50%, rgba(34,211,238,0.2) 100%)', WebkitBackgroundClip: 'text', backgroundSize: '200% 100%', animation: 'gradientShift 2s linear infinite' }}>
            KnowUrDB
          </h1>
          
          {/* Phase 4 & 5: Resolve & Light Sweep */}
          <h1 className={`text-[34px] md:text-[56px] lg:text-[72px] font-bold tracking-tight text-zinc-100 transition-all duration-1000 cubic-bezier(0.16, 1, 0.3, 1) ${showBrandResolve ? 'opacity-100 scale-100' : 'opacity-0 scale-105'}`}>
            <span className="relative inline-block overflow-hidden pb-2">
              KnowUrDB
              {/* Sweep Layer */}
              {showBrandSweep && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-40 mix-blend-overlay animate-light-sweep pointer-events-none transform -skew-x-12"></div>
              )}
            </span>
          </h1>

        </div>

        {/* Text Container */}
        <div className="flex flex-col items-center min-h-[90px]">
          {showCategory && (
            <div className="text-[10px] md:text-[11px] font-bold tracking-[0.35em] text-cyan-500/70 uppercase mb-4 opacity-0 animate-text-reveal">
              Database Intelligence Platform
            </div>
          )}
          
          {showTagline && (
            <p className="text-[11px] md:text-sm font-medium tracking-widest text-zinc-500 opacity-0 animate-text-reveal" style={{ animationDelay: '150ms' }}>
              Understand your data. Ask it anything.
            </p>
          )}
        </div>

        {/* Loading Rail (Data Energy Rail) */}
        <div className={`mt-10 w-full max-w-[240px] flex flex-col items-center relative min-h-[40px] transition-opacity duration-700 ${isExit ? 'opacity-0' : 'opacity-100'}`}>
          {showRail && (
            <div className="w-full relative h-[1px] mb-8 opacity-0 animate-rail-appear">
              {/* Base Line */}
              <div className="absolute inset-0 bg-zinc-800/40"></div>
              
              {/* Progress Flow */}
              <div className="absolute top-0 left-0 h-full bg-cyan-700/60 origin-left animate-rail-flow"></div>
              
              {/* Energy Point */}
              <div className="absolute top-1/2 -translate-y-1/2 w-4 h-[1px] bg-cyan-300 shadow-[0_0_10px_rgba(34,211,238,0.9)] animate-rail-energy origin-center rounded-full">
                {/* Micro particle sparks */}
                <div className="absolute -top-[1px] left-1/2 w-[2px] h-[2px] bg-white rounded-full animate-rail-spark"></div>
                <div className="absolute -bottom-[1px] left-1/4 w-[1px] h-[1px] bg-white rounded-full animate-rail-spark" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          )}

          {/* Status Message */}
          <div className="h-4 flex items-center justify-center relative w-full overflow-hidden">
            {showRail && STAGES.map((msg, idx) => (
              <span 
                key={idx}
                className={`absolute text-[8px] md:text-[9px] font-medium tracking-[0.25em] text-zinc-600 transition-all duration-700 ease-out uppercase
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

