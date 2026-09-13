import React, { useEffect, useRef, useState } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [isExit, setIsExit] = useState(false);
  
  // Master Animation Refs
  const rAF = useRef<number>(0);
  const startTime = useRef<number>(0);
  
  // DOM element refs for direct smooth manipulation
  const wordmarkRef = useRef<HTMLSpanElement>(null);
  const taglineRef = useRef<HTMLParagraphElement>(null);
  const railRef = useRef<HTMLDivElement>(null);
  const railHeadRef = useRef<HTMLDivElement>(null);

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

  // Master Motion Timeline (Progress 0 -> 1)
  useEffect(() => {
    const TOTAL_DURATION = 3400; // 3.4 seconds total loading sequence

    // Elegant motion curves
    const easeOutCubic = (x: number): number => 1 - Math.pow(1 - x, 3);
    const easeInOutQuad = (x: number): number => x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
    const easeInOutQuart = (x: number): number => x < 0.5 ? 8 * x * x * x * x : 1 - Math.pow(-2 * x + 2, 4) / 2;

    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp;
      const elapsed = timestamp - startTime.current;
      const progress = Math.min(elapsed / TOTAL_DURATION, 1);

      // 1. Premium Fast Ignition Wordmark Signal (3% to 30% -> ~100ms to 1020ms, ~900ms duration)
      if (wordmarkRef.current) {
        if (progress >= 0.03 && progress <= 0.3) {
          const signalP = easeInOutQuart((progress - 0.03) / 0.27);
          wordmarkRef.current.style.backgroundPosition = `${100 - (signalP * 100)}% 0`;
        } else if (progress > 0.3) {
          wordmarkRef.current.style.backgroundPosition = `0% 0`;
        }
      }

      // 2. Supporting Tagline Materialization (16% to 35% -> ~540ms to 1190ms, ~650ms duration)
      if (taglineRef.current) {
        if (progress >= 0.16 && progress <= 0.35) {
          const taglineP = easeOutCubic((progress - 0.16) / 0.19);
          taglineRef.current.style.opacity = String(taglineP);
          taglineRef.current.style.transform = `translateY(${(1 - taglineP) * 12}px)`;
          taglineRef.current.style.filter = `blur(${(1 - taglineP) * 3}px)`;
        } else if (progress > 0.35) {
          taglineRef.current.style.opacity = '1';
          taglineRef.current.style.transform = 'translateY(0px)';
          taglineRef.current.style.filter = 'blur(0px)';
        }
      }

      // 3. Data Rail Progression (6% to 82% -> ~200ms to 2780ms)
      if (railRef.current && railHeadRef.current) {
        if (progress >= 0.06 && progress <= 0.82) {
          const railP = easeInOutQuad((progress - 0.06) / 0.76);
          railRef.current.style.transform = `scaleX(${railP})`;
          railHeadRef.current.style.left = `${railP * 100}%`;
        } else if (progress > 0.82) {
          railRef.current.style.transform = `scaleX(1)`;
          railHeadRef.current.style.left = `100%`;
        }
      }

      // 3. Cinematic Exit
      if (progress < 1) {
        rAF.current = requestAnimationFrame(animate);
      } else {
        setIsExit(true);
        setTimeout(() => {
          onRevealRef.current();
        }, 300);
        setTimeout(() => {
          onCompleteRef.current();
        }, 1000);
      }
    };

    rAF.current = requestAnimationFrame(animate);

    return () => {
      if (rAF.current) cancelAnimationFrame(rAF.current);
    };
  }, []);

  // Canvas Background - Deep Galaxy (Subtle, Atmospheric)
  useEffect(() => {
    if (prefersReducedMotion) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let stars: { x: number, y: number, r: number, alpha: number, layer: number, twinklePhase: number, twinkleSpeed: number }[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initElements();
    };

    const initElements = () => {
      stars = [];
      const isMobile = window.innerWidth < 768;
      const starCount = isMobile ? 60 : 140; // Extremely sparse and tasteful
      
      for (let i = 0; i < starCount; i++) {
        const rand = Math.random();
        let layer = 1;
        if (rand > 0.9) layer = 3;
        else if (rand > 0.6) layer = 2;

        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: layer === 3 ? Math.random() * 0.6 + 0.3 : layer === 2 ? Math.random() * 0.3 + 0.2 : Math.random() * 0.2 + 0.1,
          alpha: layer === 3 ? Math.random() * 0.3 + 0.15 : layer === 2 ? Math.random() * 0.15 + 0.05 : Math.random() * 0.1,
          layer,
          twinklePhase: Math.random() * Math.PI * 2,
          twinkleSpeed: Math.random() * 0.01 + 0.005
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      if (isExit) {
        ctx.globalAlpha -= 0.015;
        if (ctx.globalAlpha < 0) ctx.globalAlpha = 0;
      }

      for (const s of stars) {
        s.twinklePhase += s.twinkleSpeed;
        let currentAlpha = s.alpha;
        
        if (s.layer === 3) {
          currentAlpha = s.alpha + Math.sin(s.twinklePhase) * 0.15;
          ctx.fillStyle = `rgba(180, 230, 255, ${Math.max(0, currentAlpha)})`;
          s.y -= 0.015; // Very slow drift
        } else if (s.layer === 2) {
          ctx.fillStyle = `rgba(255, 255, 255, ${currentAlpha})`;
          s.y -= 0.008;
        } else {
          ctx.fillStyle = `rgba(150, 150, 150, ${currentAlpha})`;
          s.y -= 0.002;
        }

        if (s.y < 0) s.y = canvas.height;

        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
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
  }, [prefersReducedMotion, isExit]);

  return (
    <div 
      className={`fixed inset-0 z-[9999] h-[100dvh] w-full flex items-center justify-center bg-[#020204] text-zinc-100 overflow-hidden select-none touch-none pointer-events-auto transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)] ${isExit ? 'opacity-0 scale-[1.03]' : 'opacity-100 scale-100'}`}
    >
      {/* Layer 0: Material Grain Overlay */}
      <div className="absolute inset-0 bg-noise z-0"></div>

      {/* Layer 1: Central Expanding Exit Light */}
      <div className={`absolute inset-0 pointer-events-none transition-all duration-1000 ease-out z-0 ${isExit ? 'bg-zinc-900/15' : 'bg-transparent'}`}></div>

      {/* Layer 2: Atmospheric Nebula */}
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-[2000ms] ease-in-out z-0 opacity-100`}>
        <div className="absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vw] max-w-[900px] max-h-[900px] rounded-full bg-[radial-gradient(circle,rgba(46,16,101,0.08)_0%,rgba(17,24,39,0)_70%)] animate-cinematic-breathe mix-blend-screen"></div>
        <div className="absolute top-[55%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[50vw] h-[50vw] max-w-[600px] max-h-[600px] rounded-full bg-[radial-gradient(circle,rgba(8,145,178,0.03)_0%,rgba(17,24,39,0)_60%)] animate-cinematic-breathe mix-blend-screen" style={{ animationDelay: '-5s' }}></div>
      </div>

      {/* Layer 3: Universe Canvas */}
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 pointer-events-none mix-blend-screen z-10"
      />

      {/* Central Content Container (Z-30) */}
      <div className="relative z-30 flex flex-col items-center justify-center w-full max-w-2xl px-4">
        
        {/* Unified Wordmark */}
        <div className="relative mb-6 flex justify-center items-center h-20 md:h-24">
          <h1 className="text-[36px] md:text-[50px] lg:text-[70px] font-bold tracking-tight flex items-center justify-center">
            <span 
              ref={wordmarkRef}
              className="text-transparent"
              style={{
                backgroundImage: 'linear-gradient(90deg, #f4f4f5 0%, #f4f4f5 45%, rgba(167,139,250,0.4) 48%, rgba(224,231,255,0.9) 49.6%, #ffffff 50%, rgba(224,231,255,0.9) 50.4%, rgba(167,139,250,0.4) 52%, #71717a 55%, #71717a 100%)',
                backgroundSize: '300% 100%',
                backgroundPosition: '100% 0', // 100% shows the right side (#71717a), 0% shows the left side (#f4f4f5)
                WebkitBackgroundClip: 'text',
                backgroundClip: 'text'
              }}
            >
              KnowUrDB
            </span>
          </h1>
        </div>

        {/* Supporting Tagline */}
        <div className="flex flex-col items-center min-h-[40px] mb-8">
          <p 
            ref={taglineRef}
            className="text-[13px] md:text-[15px] font-medium tracking-wide text-zinc-300 opacity-0 transform translate-y-3"
          >
            Turn questions into clarity.
          </p>
        </div>

        {/* Premium Data Energy Rail */}
        <div className="w-full max-w-[320px] flex flex-col items-center relative">
          <div className="w-full relative h-[1px]">
            {/* Inactive Base Track - highly visible against dark bg */}
            <div className="absolute inset-0 bg-white/15"></div>
            
            {/* Active Flow Line - width controlled exactly by progress */}
            <div 
              ref={railRef}
              className="absolute top-0 left-0 h-[1.5px] bg-zinc-200 origin-left w-full"
              style={{ transform: 'scaleX(0)' }}
            ></div>

            {/* Rail Head Point */}
            <div 
              ref={railHeadRef}
              className="absolute top-1/2 left-0 -translate-y-1/2 w-[4px] h-[4px] rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)]"
              style={{ left: '0%' }}
            >
              {/* Tiny refined tail */}
              <div className="absolute right-[4px] top-1/2 -translate-y-1/2 w-[6px] h-[1px] bg-zinc-300"></div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};


