
import { Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Workspace } from './pages/Workspace';
import { History } from './pages/History';
import { Schema } from './pages/Schema';

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Workspace />} />
        <Route path="/history" element={<History />} />
        <Route path="/schema" element={<Schema />} />
      </Routes>
    </AppShell>
  );
}

export default App;

