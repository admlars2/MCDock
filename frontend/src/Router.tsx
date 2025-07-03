import { Routes, Route, Navigate } from 'react-router-dom';
import InstancesPage from './pages/Instances';
import AuthLayout from './layouts/AuthLayout';
import CreateInstance from './pages/CreateInstance';
import Instance from './pages/instance/Instance';
import InstanceEdit from './pages/instance/InstanceEdit';
import InstanceBackups from './pages/instance/InstanceBackups';
import InstanceSchedules from './pages/instance/InstanceSchedules';

export default function Router() {
  return (
        <Routes>
            <Route path="/" element={<AuthLayout />}>
                <Route index element={<Navigate to="instances" replace />} />
                <Route path="instances" element={<InstancesPage />} />
                <Route path="instances/create" element={<CreateInstance />} />
                <Route path="/instances/:name" element={<Instance />} />
                <Route path="/instances/:name/compose" element={<InstanceEdit />} />
                <Route path="/instances/:name/backups" element={<InstanceBackups />} />
                <Route path="/instances/:name/schedules" element={<InstanceSchedules />} />
            </Route>
        </Routes>
    );
}