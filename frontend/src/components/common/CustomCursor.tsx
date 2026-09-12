import React, { useEffect, useState, useRef } from 'react';

export const CustomCursor: React.FC = () => {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const cursorRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // Check if it's a touch device or user prefers reduced motion
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (isTouchDevice || prefersReducedMotion) {
      return;
    }

    const onMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
      if (!isVisible) setIsVisible(true);
    };

    const onMouseLeave = () => {
      setIsVisible(false);
    };

    const onMouseEnter = () => {
      setIsVisible(true);
    };

    // Detect hovering over clickable elements
    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.tagName.toLowerCase() === 'button' ||
        target.tagName.toLowerCase() === 'a' ||
        target.tagName.toLowerCase() === 'input' ||
        target.tagName.toLowerCase() === 'select' ||
        target.closest('button') ||
        target.closest('a') ||
        target.classList.contains('cursor-pointer')
      ) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
    };

    window.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mouseenter', onMouseEnter);
    window.addEventListener('mouseover', handleMouseOver);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseleave', onMouseLeave);
      document.addEventListener('mouseenter', onMouseEnter);
      window.removeEventListener('mouseover', handleMouseOver);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <>
      <div 
        ref={cursorRef}
        className={`fixed top-0 left-0 pointer-events-none z-[9999] rounded-full mix-blend-difference transition-transform duration-100 ease-out`}
        style={{
          width: '24px',
          height: '24px',
          backgroundColor: '#fff',
          transform: `translate3d(${position.x - 12}px, ${position.y - 12}px, 0) scale(${isHovering ? 1.5 : 1})`,
        }}
      />
      <div 
        className={`fixed top-0 left-0 pointer-events-none z-[9998] rounded-full transition-transform duration-300 ease-out`}
        style={{
          width: '8px',
          height: '8px',
          backgroundColor: '#22d3ee',
          transform: `translate3d(${position.x - 4}px, ${position.y - 4}px, 0)`,
          opacity: isHovering ? 0 : 1,
        }}
      />
    </>
  );
};
