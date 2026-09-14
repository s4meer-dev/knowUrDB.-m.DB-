import '@testing-library/jest-dom';

// jsdom does not implement window.matchMedia — polyfill for components
// that use it (CustomCursor, CinematicIntro reduced-motion detection)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
