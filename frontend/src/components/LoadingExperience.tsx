import React, { useEffect, useRef, useState } from 'react';

interface LoadingExperienceProps {
  onReveal: () => void;
  onComplete: () => void;
}

const STAGES = [
  "INITIALIZING INTELLIGENCE",
  "CONNECTING TO DATA LAYER",
  "UNDERSTANDING DATABASE STRUCTURE",
  "PREPARING WORKSPACE"
];

export const LoadingExperience: React.FC<LoadingExperienceProps> = ({ onReveal, onComplete }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stageIndex, setStageIndex] = useState(0);
  const [isExiting, setIsExiting] = useState(false);
  const [isRevealingApp, setIsRevealingApp] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  // Handle prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Message lifecycle (total ~3.6 seconds + 1s exit)
  useEffect(() => {
    const intervalTime = 900; // 900ms per stage
    let currentStage = 0;
    
    const interval = setInterval(() => {
      currentStage++;
      if (currentStage < STAGES.length) {
        setStageIndex(currentStage);
      } else {
        clearInterval(interval);
        // Start exit sequence
        setIsExiting(true);
        
        // Wait for secondary elements to fade, then reveal app
        setTimeout(() => {
          setIsRevealingApp(true);
          onReveal();
        }, 600);

        // Tell parent to remove us completely after transition finishes
        setTimeout(() => {
          onComplete();
        }, 1300);
      }
    }, intervalTime);

    return () => clearInterval(interval);
  }, [onReveal, onComplete]);

  // Canvas background metaphor (Nodes & Connections)
  useEffect(() => {
    if (prefersReducedMotion) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: { x: number, y: number, vx: number, vy: number }[] = [];
    
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initParticles();
    };

    const initParticles = () => {
      particles = [];
      const numParticles = Math.floor((canvas.width * canvas.height) / 30000); // Very sparse
      for (let i = 0; i < Math.min(numParticles, 50); i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.2, // Extremely slow
          vy: (Math.random() - 0.5) * 0.2
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Update & draw particles
      ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, 1, 0, Math.PI * 2);
        ctx.fill();

        // Draw connections
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 150) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(34, 211, 238, ${0.05 * (1 - dist / 150)})`; // subtle cyan
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

  return (
    <div 
      className={`fixed inset-0 z-[100] flex items-center justify-center bg-[#050507] text-zinc-100 overflow-hidden select-none transition-opacity duration-700 ease-in-out ${isRevealingApp ? 'opacity-0' : 'opacity-100'}`}
    >
      {/* Subtle radial glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-violet-900/5 blur-[120px] animate-pulse-slow"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-cyan-900/5 blur-[80px]"></div>
      </div>

      {/* Canvas Background Metaphor */}
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 pointer-events-none opacity-60"
      />

      {/* Micro details */}
      <div className={`absolute top-8 left-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-700 ${isExiting ? 'opacity-0' : 'animate-fade-in'}`}>
        KNOWURDB SYSTEM INITIALIZATION
      </div>
      <div className={`absolute bottom-8 left-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-700 ${isExiting ? 'opacity-0' : 'animate-fade-in'}`}>
        DATABASE INTELLIGENCE PLATFORM
      </div>
      <div className={`absolute bottom-8 right-8 text-[10px] font-mono tracking-widest text-zinc-600 transition-opacity duration-700 ${isExiting ? 'opacity-0' : 'animate-fade-in'}`}>
        v1.0
      </div>

      {/* Central Content */}
      <div className={`relative z-10 flex flex-col items-center justify-center -mt-16 w-full max-w-lg transition-transform duration-1000 ease-out ${isRevealingApp ? 'scale-105' : 'scale-100'}`}>
        
        {/* Brand Logo Reveal */}
        <div className="relative mb-2">
          <h1 className="text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-zinc-200 animate-brand-reveal relative">
            knowUrDB
            {/* Horizontal light sweep */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 mix-blend-overlay animate-light-sweep pointer-events-none"></div>
          </h1>
        </div>

        {/* Subtitle */}
        <div className={`mb-12 transition-opacity duration-500 delay-300 ${isExiting ? 'opacity-0' : 'animate-fade-in'}`}>
          <p className="text-xs font-medium tracking-[0.2em] uppercase text-zinc-500">
            Understand your data. Ask it anything.
          </p>
        </div>

        {/* Loading Indicator & Stages */}
        <div className={`w-full max-w-[240px] flex flex-col items-center transition-opacity duration-500 ${isExiting ? 'opacity-0' : 'opacity-100'}`}>
          
          {/* Custom minimal line indicator */}
          <div className="w-full h-[1px] bg-zinc-800/50 relative overflow-hidden mb-6">
            <div className="absolute top-0 left-0 h-full w-1/3 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-loading-line"></div>
          </div>

          {/* Messages */}
          <div className="h-4 flex items-center justify-center relative w-full overflow-hidden mb-8">
            {STAGES.map((msg, idx) => (
              <span 
                key={idx}
                className={`absolute text-[10px] font-bold tracking-[0.15em] text-cyan-500/80 transition-all duration-500 ease-out uppercase
                  ${idx === stageIndex ? 'opacity-100 transform-none' : 
                    idx < stageIndex ? 'opacity-0 -translate-y-4' : 'opacity-0 translate-y-4'}`}
              >
                {msg}
              </span>
            ))}
          </div>

          {/* Stage Progress */}
          <div className="text-[10px] font-mono tracking-widest text-zinc-600">
            0{stageIndex + 1} / 0{STAGES.length}
          </div>

        </div>

      </div>
    </div>
  );
};
