import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import DatasetDetailsPage from './pages/DatasetDetailsPage';
import PipelinesPage from './pages/PipelinesPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/pipelines" element={<PipelinesPage />} />
        <Route path="/datasets/:id" element={<DatasetDetailsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
