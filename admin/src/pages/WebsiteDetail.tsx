import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import type { Website } from "../api/types";
import FlowsPanel from "./FlowsPanel";
import KnowledgePanel from "./KnowledgePanel";
import ConversationsPanel from "./ConversationsPanel";
import ReportingPanel from "./ReportingPanel";
import EmbedPanel from "./EmbedPanel";

const TABS = ["Overview", "Flows", "Knowledge", "Conversations", "Reporting", "Embed"] as const;
type Tab = (typeof TABS)[number];

export default function WebsiteDetail() {
  const { id } = useParams<{ id: string }>();
  const [website, setWebsite] = useState<Website | null>(null);
  const [tab, setTab] = useState<Tab>("Overview");

  function load() {
    if (id) api.get<Website>(`/api/websites/${id}`).then(setWebsite);
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (!website) return <p>Loading...</p>;

  return (
    <div>
      <p>
        <Link to="/websites">← Back to Websites</Link>
      </p>
      <h1>{website.name}</h1>
      <p className="muted">
        {website.url} · <span className={`status-badge status-${website.status}`}>{website.status}</span> ·{" "}
        {website.page_count} pages
      </p>
      {website.error_message && <p className="error-text">{website.error_message}</p>}

      <div className="tab-bar">
        {TABS.map((t) => (
          <button key={t} className={tab === t ? "tab active" : "tab"} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {tab === "Overview" && (
          <div className="card">
            <p>
              <strong>Website ID:</strong> {website.website_id}
            </p>
            <p>
              <strong>Max pages:</strong> {website.max_pages} &nbsp; <strong>Max depth:</strong> {website.max_depth}
            </p>
            <p>
              <strong>Created:</strong> {new Date(website.created_at).toLocaleString()}
            </p>
          </div>
        )}
        {tab === "Flows" && <FlowsPanel websiteId={website.website_id} />}
        {tab === "Knowledge" && <KnowledgePanel websiteId={website.website_id} websiteName={website.name} />}
        {tab === "Conversations" && <ConversationsPanel websiteId={website.website_id} />}
        {tab === "Reporting" && <ReportingPanel websiteId={website.website_id} />}
        {tab === "Embed" && <EmbedPanel websiteId={website.website_id} websiteName={website.name} />}
      </div>
    </div>
  );
}
