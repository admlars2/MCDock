import { Routes, Route, Navigate } from 'react-router-dom';
import InstancesPage from './pages/Instances';

export default function App() {
  return (
        <Routes>
            <Route path="/" element={<Navigate to="/instances" />} />
            <Route path="/instances" element={<InstancesPage />} />
        </Routes>
    );
}
