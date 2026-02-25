import { Routes, Route, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  DollarSign,
  Server,
  Users,
  Bell,
  FileText,
  Lightbulb,
  TrendingUp,
  Tag,
  Building2,
} from "lucide-react";
import Dashboard from "./pages/Dashboard";
import CostsPage from "./pages/CostsPage";
import ClustersPage from "./pages/ClustersPage";
import TeamsPage from "./pages/TeamsPage";
import AlertsPage from "./pages/AlertsPage";
import ReportsPage from "./pages/ReportsPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import ForecastPage from "./pages/ForecastPage";

function App() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>CostPulse</h1>
          <p>FinOps for Databricks</p>
        </div>
        <nav>
          <ul className="sidebar-nav">
            <li className="sidebar-section-title">Overview</li>
            <li>
              <NavLink to="/" end>
                <LayoutDashboard size={18} /> Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink to="/costs">
                <DollarSign size={18} /> Cost Explorer
              </NavLink>
            </li>
            <li>
              <NavLink to="/forecast">
                <TrendingUp size={18} /> Forecasting
              </NavLink>
            </li>

            <li className="sidebar-section-title">Resources</li>
            <li>
              <NavLink to="/clusters">
                <Server size={18} /> Clusters
              </NavLink>
            </li>
            <li>
              <NavLink to="/teams">
                <Users size={18} /> Teams
              </NavLink>
            </li>

            <li className="sidebar-section-title">Governance</li>
            <li>
              <NavLink to="/recommendations">
                <Lightbulb size={18} /> Recommendations
              </NavLink>
            </li>
            <li>
              <NavLink to="/alerts">
                <Bell size={18} /> Alerts
              </NavLink>
            </li>
            <li>
              <NavLink to="/reports">
                <FileText size={18} /> Reports
              </NavLink>
            </li>
          </ul>
        </nav>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/costs" element={<CostsPage />} />
          <Route path="/clusters" element={<ClustersPage />} />
          <Route path="/teams" element={<TeamsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
