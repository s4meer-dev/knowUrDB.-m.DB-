import { useEffect, useState } from 'react';
import { checkHealth } from './services/api';
import type { HealthResponse } from './types';

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const data = await checkHealth();
        if (isMounted) {
          setHealth(data);
          setError(null);
        }
      } catch {
        if (isMounted) {
          setError('Unable to reach the backend API.');
          setHealth(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4 font-sans text-gray-800">
      <div className="max-w-md w-full bg-white shadow-lg rounded-xl overflow-hidden">
        <div className="p-8 text-center">
          <h1 className="text-3xl font-bold text-indigo-600 mb-2">knowUrDB</h1>
          <p className="text-gray-500 mb-8">Natural Language Database Intelligence</p>
          
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between border border-gray-100">
              <span className="font-medium text-gray-700">Backend Status</span>
              {loading ? (
                <span className="text-gray-500 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 animate-pulse"></span>
                  Checking backend...
                </span>
              ) : health ? (
                <span className="text-green-600 flex items-center gap-2 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500"></span>
                  Connected
                </span>
              ) : (
                <span className="text-red-600 flex items-center gap-2 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span>
                  Disconnected
                </span>
              )}
            </div>

            <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between border border-gray-100">
              <span className="font-medium text-gray-700">API Status</span>
              {loading ? (
                <span className="text-gray-500">Checking...</span>
              ) : health ? (
                <span className="text-green-600 font-medium">Healthy</span>
              ) : (
                <span className="text-red-600 text-sm">{error}</span>
              )}
            </div>

            <div className="bg-gray-50 rounded-lg p-4 flex items-center justify-between border border-gray-100">
              <span className="font-medium text-gray-700">Environment</span>
              <span className="text-gray-600 bg-gray-200 px-2 py-1 rounded text-sm">Development</span>
            </div>
          </div>
        </div>
        
        <div className="bg-indigo-50 p-4 text-center border-t border-indigo-100">
          <span className="text-indigo-800 text-sm font-medium">Phase 1 &mdash; Full-Stack Foundation</span>
        </div>
      </div>
    </div>
  );
}

export default App;
