/**
 * Picks the dashboard for the logged-in user's role.
 * Place in: src/routes/dynamicRoute.tsx  (replaces the existing file)
 */
import { Navigate } from "react-router";
import { all_routes } from "./all_routes";
import { getStoredUser } from "../pages/dashboards/Dashboardshared";
import { resolveDashboardKey } from "../pages/dashboards/Dashboardconfig";
import RoleDashboard from "../pages/dashboards/Roledashboard";
import AgrovetDashboard from "../pages/dashboards/Agrovetdashboard";

const DynamicDashboardWrapper = () => {
  // The login page stores the user in sessionStorage under "user"
  const user = getStoredUser();

  if (!user) {
    return <Navigate to={all_routes.login} replace />;
  }

  const key = resolveDashboardKey(user);

  if (key === "agrovet") {
    return <AgrovetDashboard />;
  }

  if (key) {
    return <RoleDashboard roleKey={key} />;
  }

  return (
    <div className="page-wrapper">
      <div className="content">
        <div className="alert alert-warning">
          No dashboard is configured for the role "{String(user.role ?? "unknown")}".
        </div>
      </div>
    </div>
  );
};

export default DynamicDashboardWrapper;
