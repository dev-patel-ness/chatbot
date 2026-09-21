import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Website } from "../api/types";

export default function Dashboard() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Website[]>("/api/websites").then((data) => {
      setWebsites(data);
      setLoading(false);
    });
  }, []);

  const ready = websites.filter((w) => w.status === "ready").length;
  const inProgress = websites.filter((w) => !["ready", "failed"].includes(w.status)).length;
  const failed = websites.filter((w) => w.status === "failed").length;

  return (
    <div>
      <h1>Dashboard</h1>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-value">{websites.length}</div>
              <div className="stat-label">Total Websites</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{ready}</div>
              <div className="stat-label">Ready</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{inProgress}</div>
              <div className="stat-label">In Progress</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{failed}</div>
              <div className="stat-label">Failed</div>
            </div>
          </div>
          <p>
            <Link to="/websites">Manage websites →</Link>
          </p>
        </>
      )}
    </div>
  );
}
