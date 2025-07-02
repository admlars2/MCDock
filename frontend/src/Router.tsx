import { Routes, Route, Navigate } from 'react-router-dom';
import InstancesPage from './pages/Instances';
import SchedulesPage from './pages/Schedules'; 
import AuthLayout from './layouts/AuthLayout';
import CreateInstance from './pages/CreateInstance';
import InstancePage from './pages/Instance';
import EditInstance from './pages/EditInstance';

export default function Router() {
  return (
        <Routes>
            <Route path="/" element={<AuthLayout />}>
                <Route index element={<Navigate to="instances" replace />} />
                <Route path="instances" element={<InstancesPage />} />
                <Route path="instances/create" element={<CreateInstance />} />
                <Route path="/instances/:name" element={<InstancePage />} />
                <Route path="/instances/compose/:name" element={<EditInstance />} />
                <Route path="schedules" element={<SchedulesPage />} />
            </Route>
        </Routes>
    );
}