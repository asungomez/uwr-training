import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from './context'

/** Layout route that only renders its nested routes for admins; everyone else is
 * redirected to /entrenamientos. Use as a parent route's `element`:
 *
 *   <Route path="/usuarios" element={<AdminRoute />}>
 *     <Route index element={<UsersPage />} />
 *   </Route>
 */
function AdminRoute() {
  const { user } = useAuth()
  if (user?.role !== 'admin') {
    return <Navigate to="/entrenamientos" replace />
  }
  return <Outlet />
}

export default AdminRoute
