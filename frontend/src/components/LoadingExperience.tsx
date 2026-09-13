import React, { useEffect, useRef, useState } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

const STAGES = [
  "PREPARING INTELLIGENCE ENVIRONMENT",
  "INITIALIZING WORKSPACE",
  "READY"
];

type Phase = 
  | 'void' 
  | 'stars' 
  | 'atmosphere' 
  | 'network' 
  | 'brand_fragments' 
  | 'brand_traces' 
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
    const timeline = [
      { t: 350, p: 'stars' as Phase },
      { t: 600, p: 'atmosphere' as Phase },
      { t: 900, p: 'network' as Phase },
      { t: 1200, p: 'brand_fragments' as Phase },
      { t: 1500, p: 'brand_traces' as Phase },
      { t: 1900, p: 'brand_energy' as Phase },
      { t: 2400, p: 'brand_resolve' as Phase },
      { t: 2700, p: 'brand_sweep' as Phase },
      { t: 2900, p: 'category' as Phase },
      { t: 3100, p: 'tagline' as Phase },
      { t: 3400, p: 'rail' as Phase },
      { t: 4000, p: 'ready' as Phase },
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
    }, 5500);

    return () => {
      timeouts.forEach(clearTimeout);
      clearTimeout(revealTimeout);
      clearTimeout(unmountTimeout);
    };
  }, []); // <-- Empty array: GUARANTEED to run exactly once on mount

  // Status Message Master Timeline Sync
  useEffect(() => {
    if (phase === 'rail') setStageIndex(0);
    else if (phase === 'ready') setStageIndex(2);
    else if (phase === 'exit') setStageIndex(2);
  }, [phase]);

  // Canvas background metaphor (Intelligent Schema / Data Nodes / Stars)
  useEffect(() => {
    if (prefersReducedMotion) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let stars: { x: number, y: number, r: number, alpha: number, layer: number, twinklePhase: number, twinkleSpeed: number }[] = [];
    let nodes: { x: number, y: number, vx: number, vy: number, r: number, isCore: boolean, alpha: number }[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initElements();
    };

    const initElements = () => {
      stars = [];
      nodes = [];
      
      const isMobile = window.innerWidth < 768;
      const starCount = isMobile ? 100 : 250;
      const nodeCount = isMobile ? 15 : 35; // Sparse, sophisticated network
      
      // Init Stars - Multiple Depths
      for (let i = 0; i < starCount; i++) {
        const rand = Math.random();
        let layer = 1;
        if (rand > 0.85) layer = 3;
        else if (rand > 0.5) layer = 2;

        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: layer === 3 ? Math.random() * 0.8 + 0.4 : layer === 2 ? Math.random() * 0.5 + 0.2 : Math.random() * 0.3 + 0.1,
          alpha: layer === 3 ? Math.random() * 0.5 + 0.3 : layer === 2 ? Math.random() * 0.3 + 0.1 : Math.random() * 0.2,
          layer,
          twinklePhase: Math.random() * Math.PI * 2,
          twinkleSpeed: Math.random() * 0.02 + 0.005
        });
      }
      
      // Init Nodes - Data Intelligence Field
      for (let i = 0; i < nodeCount; i++) {
        nodes.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.08,
          vy: (Math.random() - 0.5) * 0.08,
          r: Math.random() * 0.8 + 0.4,
          isCore: Math.random() > 0.75,
          alpha: 0
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      
      const pIdx = ['void', 'stars', 'atmosphere', 'network', 'brand_fragments', 'brand_traces', 'brand_energy', 'brand_resolve', 'brand_sweep', 'category', 'tagline', 'rail', 'ready', 'exit'].indexOf(phase);
      
      const showStars = pIdx >= 1;
      const showNodes = pIdx >= 3;
      const isConverging = pIdx >= 4 && pIdx <= 12; // Pull inward during formation
      const isExit = pIdx >= 13;

      if (isExit) {
        ctx.globalAlpha -= 0.015;
        if (ctx.globalAlpha < 0) ctx.globalAlpha = 0;
      }

      // Draw Stars
      if (showStars) {
        for (const s of stars) {
          s.twinklePhase += s.twinkleSpeed;
          let currentAlpha = s.alpha;
          
          if (s.layer === 3) {
            // Twinkle effect on layer 3
            currentAlpha = s.alpha + Math.sin(s.twinklePhase) * 0.2;
            ctx.fillStyle = `rgba(180, 230, 255, ${Math.max(0, currentAlpha)})`;
            s.y -= 0.04; // Drift
          } else if (s.layer === 2) {
            ctx.fillStyle = `rgba(255, 255, 255, ${currentAlpha})`;
            s.y -= 0.015;
          } else {
            ctx.fillStyle = `rgba(150, 150, 150, ${currentAlpha})`;
            s.y -= 0.005;
          }

          if (s.y < 0) s.y = canvas.height;

          ctx.beginPath();
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Draw Data Universe (Abstract Network)
      if (showNodes) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
        for (let i = 0; i < nodes.length; i++) {
          const p = nodes[i];
          
          // Fade in nodes gently
          if (p.alpha < 1) p.alpha += 0.01;

          if (isConverging && p.isCore) {
            const dx = centerX - p.x;
            const dy = centerY - p.y;
            // Easing towards center
            p.x += dx * 0.0015;
            p.y += dy * 0.0015;
          } else {
            p.x += p.vx;
            p.y += p.vy;
          }

          // Boundary wrap
          if (p.x < 0) p.x = canvas.width;
          if (p.x > canvas.width) p.x = 0;
          if (p.y < 0) p.y = canvas.height;
          if (p.y > canvas.height) p.y = 0;

          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fill();

          // Connect nodes
          for (let j = i + 1; j < nodes.length; j++) {
            const p2 = nodes[j];
            const dx = p.x - p2.x;
            const dy = p.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            // Sophisticated connection threshold
            if (dist < 150) {
              ctx.beginPath();
              // Extremely faint connections, tint with cyan/violet based on distance
              const lineAlpha = 0.03 * (1 - dist / 150) * p.alpha;
              ctx.strokeStyle = `rgba(167, 139, 250, ${lineAlpha})`; 
              ctx.lineWidth = 0.4;
              ctx.moveTo(p.x, p.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.stroke();
              
              // Draw moving signals along connections occasionally
              if (dist > 50 && Math.sin(p.x + p2.y + Date.now()/500) > 0.95) {
                const signalProgress = (Date.now() % 2000) / 2000;
                const sigX = p.x + (p2.x - p.x) * signalProgress;
                const sigY = p.y + (p2.y - p.y) * signalProgress;
                ctx.beginPath();
                ctx.fillStyle = `rgba(34, 211, 238, ${lineAlpha * 4})`;
                ctx.arc(sigX, sigY, 1, 0, Math.PI * 2);
                ctx.fill();
              }
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

  const pIdx = ['void', 'stars', 'atmosphere', 'network', 'brand_fragments', 'brand_traces', 'brand_energy', 'brand_resolve', 'brand_sweep', 'category', 'tagline', 'rail', 'ready', 'exit'].indexOf(phase);
  
  const showAtmosphere = pIdx >= 2;
  const showBrandFragments = pIdx >= 4;
  const showBrandTraces = pIdx >= 5;
  const showBrandEnergy = pIdx >= 6;
  const showBrandResolve = pIdx >= 7;
  const showBrandSweep = pIdx >= 8 && pIdx < 13;
  const showCategory = pIdx >= 9;
  const showTagline = pIdx >= 10;
  const showRail = pIdx >= 11;
  const isReady = pIdx >= 12;
  const isExit = pIdx >= 13;

  return (
    <div 
      className={`fixed inset-0 z-[9999] h-[100dvh] w-full flex items-center justify-center bg-[#020204] text-zinc-100 overflow-hidden select-none touch-none pointer-events-auto transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)] ${isExit ? 'opacity-0 scale-[1.03]' : 'opacity-100 scale-100'}`}
    >
      {/* Layer 0: Material Grain Overlay */}
      <div className="absolute inset-0 bg-noise z-0"></div>

      {/* Layer 1: Central Expanding Exit Light */}
      <div className={`absolute inset-0 pointer-events-none transition-all duration-1000 ease-out z-0 ${isExit ? 'bg-zinc-900/15' : 'bg-transparent'}`}></div>

      {/* Layer 2: Atmospheric Nebula (Deep Violet/Cyan) */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-[2000ms] ease-in-out z-0 ${showAtmosphere ? 'opacity-100' : 'opacity-0'}`}>
        <div className="absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vw] max-w-[900px] max-h-[900px] rounded-full bg-[radial-gradient(circle,rgba(46,16,101,0.12)_0%,rgba(17,24,39,0)_70%)] animate-cinematic-breathe mix-blend-screen"></div>
        <div className="absolute top-[55%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[50vw] h-[50vw] max-w-[600px] max-h-[600px] rounded-full bg-[radial-gradient(circle,rgba(8,145,178,0.04)_0%,rgba(17,24,39,0)_60%)] animate-cinematic-breathe mix-blend-screen" style={{ animationDelay: '-5s' }}></div>
      </div>

      {/* Layer 3: Universe Canvas (Stars & Data) */}
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 pointer-events-none mix-blend-screen z-10"
      />

      {/* Micro UI / Technical Instrumentation */}
      <div className="absolute inset-0 pointer-events-none z-20 p-6 md:p-8 flex flex-col justify-between text-[9px] md:text-[10px] font-mono tracking-widest text-zinc-500/30 uppercase opacity-0 animate-fade-in" style={{ animationDelay: '1s' }}>
        <div className="flex justify-between w-full">
          <div>
            KNOWURDB<br/>
            INTELLIGENCE SYSTEM
          </div>
          <div className="text-right">
            SEQ-001
          </div>
        </div>
        <div className="flex justify-between w-full">
          <div>
            NATURAL LANGUAGE → DATABASE
          </div>
          <div className="text-right transition-colors duration-700">
            {isReady ? <span className="text-cyan-500/50">READY</span> : <span>INITIALIZING</span>}
          </div>
        </div>
      </div>

      {/* Central Content Container (Z-30) */}
      <div className="relative z-30 flex flex-col items-center justify-center w-full max-w-2xl px-4">
        
        {/* Wordmark Optical Container */}
        <div className="relative mb-6 flex justify-center items-center h-20 md:h-24">
          
          <h1 className="text-[34px] md:text-[46px] lg:text-[64px] font-bold tracking-tight relative">
            
            {/* Phase 1 & 2: Fragments & Traces (Stroked, low opacity, blurry) */}
            <span 
              className={`absolute inset-0 transition-all duration-1000 ease-out 
                ${showBrandFragments && !showBrandResolve ? 'opacity-100 blur-[1px]' : 'opacity-0 blur-md scale-[0.98]'}`}
              style={{ 
                WebkitTextStroke: showBrandTraces ? '1px rgba(167, 139, 250, 0.6)' : '1px rgba(255, 255, 255, 0.1)',
                color: 'transparent'
              }}
            >
              KnowUrDB
            </span>

            {/* Phase 3: Brand Energy (Internal Fill) */}
            <span 
              className={`absolute inset-0 transition-all duration-700 ease-out bg-clip-text
                ${showBrandEnergy && !showBrandResolve ? 'opacity-100 scale-100 blur-[0.5px]' : 'opacity-0 scale-[0.99] blur-[4px]'}`}
              style={{ 
                backgroundImage: 'linear-gradient(90deg, rgba(34,211,238,0.2) 0%, rgba(167,139,250,0.8) 50%, rgba(34,211,238,0.2) 100%)', 
                WebkitBackgroundClip: 'text', 
                color: 'transparent',
                backgroundSize: '200% 100%', 
                animation: 'gradientShift 2.5s linear infinite' 
              }}
            >
              KnowUrDB
            </span>

            {/* Phase 4 & 5: Resolve & Sweep (Crisp White) */}
            <span 
              className={`relative inline-block overflow-hidden transition-all duration-1000 ease-[cubic-bezier(0.16,1,0.3,1)]
                ${showBrandResolve ? 'opacity-100 scale-100' : 'opacity-0 scale-[1.02]'}`}
              style={{ color: '#f4f4f5' }}
            >
              KnowUrDB
              {/* Elegant Light Sweep */}
              {showBrandSweep && (
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent mix-blend-overlay animate-light-sweep pointer-events-none"></div>
              )}
            </span>

          </h1>
        </div>

        {/* Supporting Information Container */}
        <div className="flex flex-col items-center min-h-[90px]">
          {showCategory && (
            <div className="text-[9px] md:text-[10px] font-bold text-cyan-500/70 uppercase mb-4 animate-tracking-settle">
              Database Intelligence Platform
            </div>
          )}
          
          {showTagline && (
            <p className="text-[11px] md:text-[13px] font-medium tracking-widest text-zinc-400 opacity-0 animate-text-reveal" style={{ animationDelay: '100ms' }}>
              Understand your data. Ask it anything.
            </p>
          )}
        </div>

        {/* Intelligence Rail */}
        <div className={`mt-8 w-full max-w-[280px] flex flex-col items-center relative min-h-[50px] transition-opacity duration-700 ease-out ${isExit ? 'opacity-0' : 'opacity-100'}`}>
          
          {/* Main Rail Track */}
          <div className={`w-full relative h-[1px] mb-8 transition-opacity duration-700 ${showRail ? 'opacity-100' : 'opacity-0'}`}>
            
            {/* 1px Base Track */}
            <div className="absolute inset-0 bg-white/10"></div>
            
            {/* Active Flow Line */}
            <div className={`absolute top-0 left-0 h-[1.5px] bg-cyan-500/80 origin-left shadow-[0_0_8px_rgba(34,211,238,0.5)] ${showRail ? 'animate-rail-flow' : ''}`}>
              
              {/* Rail Head Energy Point */}
              <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-white shadow-[0_0_12px_rgba(255,255,255,1)]">
                {/* Micro Particles */}
                <div className="absolute -top-[3px] -left-[2px] w-[1px] h-[1px] bg-white rounded-full animate-rail-spark"></div>
                <div className="absolute -bottom-[3px] -left-[4px] w-[1.5px] h-[1px] bg-cyan-200 rounded-full animate-rail-spark" style={{ animationDelay: '400ms' }}></div>
              </div>

            </div>
          </div>

          {/* Precision Status Labels */}
          <div className="h-4 flex items-center justify-center relative w-full overflow-hidden">
            {showRail && STAGES.map((msg, idx) => (
              <span 
                key={idx}
                className={`absolute text-[8px] md:text-[9px] font-medium tracking-[0.3em] text-zinc-500 transition-all duration-[800ms] ease-[cubic-bezier(0.16,1,0.3,1)] uppercase
                  ${idx === stageIndex ? 'opacity-100 transform-none blur-none' : 
                    idx < stageIndex ? 'opacity-0 -translate-y-4 blur-[2px]' : 'opacity-0 translate-y-4 blur-[2px]'}`}
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

