import { Routes, Route, Navigate } from 'react-router-dom';
import InstancesPage from './pages/Instances';
import SchedulesPage from './pages/Schedules'; 
import AuthLayout from './layouts/AuthLayout';
import CreateInstance from './pages/CreateInstance';
import InstancePage from './pages/instance/Instance';
import EditInstance from './pages/instance/EditInstance';
import InstanceBackupsPage from './pages/instance/InstanceBackups';

export default function Router() {
  return (
        <Routes>
            <Route path="/" element={<AuthLayout />}>
                <Route index element={<Navigate to="instances" replace />} />
                <Route path="instances" element={<InstancesPage />} />
                <Route path="instances/create" element={<CreateInstance />} />
                <Route path="/instances/:name" element={<InstancePage />} />
                <Route path="/instances/:name/compose" element={<EditInstance />} />
                <Route path="/instances/:name/backups" element={<InstanceBackupsPage />} />
                <Route path="schedules" element={<SchedulesPage />} />
            </Route>
        </Routes>
    );
}