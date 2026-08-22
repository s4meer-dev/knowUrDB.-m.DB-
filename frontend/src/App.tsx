import { useEffect, useState } from 'react';
import { checkHealth, queryDatabase } from './services/api';
import type { HealthResponse, QueryResponse } from './types';

const EXAMPLES = [
  "How many students are in the database?",
  "Which department has the most students?",
  "List the top 5 students with the highest average score.",
  "What is the average attendance percentage per department?"
];

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendLoading, setBackendLoading] = useState<boolean>(true);
  
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [showSql, setShowSql] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const fetchHealth = async () => {
      try {
        setBackendLoading(true);
        const data = await checkHealth();
        if (isMounted) {
          setHealth(data);
        }
      } catch {
        if (isMounted) {
          setHealth(null);
        }
      } finally {
        if (isMounted) {
          setBackendLoading(false);
        }
      }
    };

    fetchHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleQuery = async (q: string = question) => {
    if (!q.trim()) return;
    
    setQuestion(q);
    setLoading(true);
    setResult(null);
    setShowSql(false);
    
    try {
      const res = await queryDatabase(q);
      setResult(res);
    } catch (e: any) {
      setResult({
        question: q,
        columns: [],
        rows: [],
        row_count: 0,
        execution_time_ms: 0,
        status: 'error',
        error: e?.response?.data?.detail || e.message || 'An unexpected error occurred.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-800">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <div>
          <h1 className="text-2xl font-bold text-indigo-600">knowUrDB</h1>
          <p className="text-sm text-gray-500">Ask questions about your database in natural language</p>
        </div>
        <div className="flex items-center space-x-2 text-sm">
          {backendLoading ? (
            <span className="text-gray-500 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
              Checking backend...
            </span>
          ) : health ? (
            <span className="text-green-600 flex items-center gap-1 font-medium">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              Connected
            </span>
          ) : (
            <span className="text-red-600 flex items-center gap-1 font-medium">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              Disconnected
            </span>
          )}
        </div>
      </header>

      <main className="flex-grow p-4 md:p-8 max-w-5xl mx-auto w-full flex flex-col space-y-6">
        
        {/* Input Area */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex flex-col space-y-4">
            <textarea
              className="w-full border border-gray-300 rounded-lg p-4 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all resize-none h-24"
              placeholder="Ask a question about the university database..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleQuery();
                }
              }}
              disabled={loading || (!health && !backendLoading)}
            />
            
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map((ex, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuery(ex)}
                    disabled={loading || (!health && !backendLoading)}
                    className="text-xs bg-indigo-50 text-indigo-600 border border-indigo-100 hover:bg-indigo-100 px-3 py-1.5 rounded-full transition-colors disabled:opacity-50"
                  >
                    {ex}
                  </button>
                ))}
              </div>
              
              <button
                onClick={() => handleQuery()}
                disabled={!question.trim() || loading || (!health && !backendLoading)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Executing
                  </>
                ) : 'Ask Database'}
              </button>
            </div>
          </div>
        </div>

        {/* Results Area */}
        <div className="flex-grow">
          {!result && !loading && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 p-12 text-center border-2 border-dashed border-gray-200 rounded-xl bg-gray-50">
              <svg className="w-12 h-12 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <p className="text-lg">No results to display.</p>
              <p className="text-sm mt-1">Ask a question above to get started.</p>
            </div>
          )}

          {result && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-[500px]">
              
              {/* Result Header */}
              <div className="bg-gray-50 border-b border-gray-200 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-gray-800">Query Result</h2>
                  {result.status === 'success' && (
                    <p className="text-xs text-gray-500 mt-1">
                      {result.row_count} row{result.row_count !== 1 ? 's' : ''} returned in {result.execution_time_ms}ms
                    </p>
                  )}
                </div>
                
                {result.generated_sql && (
                  <button
                    onClick={() => setShowSql(!showSql)}
                    className="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center"
                  >
                    <svg className={`w-4 h-4 mr-1 transition-transform ${showSql ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                    {showSql ? 'Hide SQL' : 'Show SQL'}
                  </button>
                )}
              </div>

              {/* SQL Panel */}
              {showSql && result.generated_sql && (
                <div className="bg-gray-900 text-gray-100 p-4 border-b border-gray-200 overflow-x-auto">
                  <pre className="text-sm font-mono whitespace-pre-wrap">
                    {result.generated_sql}
                  </pre>
                </div>
              )}

              {/* Result Body */}
              <div className="flex-grow overflow-auto p-0">
                {result.status === 'error' ? (
                  <div className="p-6">
                    <div className="bg-red-50 text-red-700 border border-red-200 p-4 rounded-lg flex items-start">
                      <svg className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                      <div>
                        <h4 className="font-semibold">Query Error</h4>
                        <p className="text-sm mt-1">{result.error}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="min-w-full">
                    {result.columns.length > 0 ? (
                      <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
                        <thead className="bg-gray-50 sticky top-0 shadow-sm">
                          <tr>
                            {result.columns.map((col, idx) => (
                              <th key={idx} className="px-6 py-3 font-semibold text-gray-700 tracking-wider">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                          {result.rows.map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-gray-50 transition-colors">
                              {result.columns.map((col, cIdx) => (
                                <td key={cIdx} className="px-6 py-4 whitespace-nowrap text-gray-600">
                                  {row[col] !== null ? String(row[col]) : <span className="text-gray-400 italic">null</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                          {result.rows.length === 0 && (
                            <tr>
                              <td colSpan={result.columns.length} className="px-6 py-8 text-center text-gray-500">
                                The query executed successfully but returned 0 rows.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    ) : (
                       <div className="p-6 text-center text-gray-500">
                          No columns returned.
                       </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
