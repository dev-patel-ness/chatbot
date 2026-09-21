import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Website } from "../api/types";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  crawling: "Crawling",
  understanding: "Understanding",
  embedding: "Embedding",
  discovering_flows: "Discovering Flows",
  ready: "Ready",
  failed: "Failed",
};

export default function Websites() {
  const [websites, setWebsites] = useState<Website[]>([]);
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [maxPages, setMaxPages] = useState(25);
  const [maxDepth, setMaxDepth] = useState(2);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api.get<Website[]>("/api/websites").then(setWebsites);
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000); // poll for pipeline status updates
    return () => clearInterval(interval);
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      await api.post("/api/websites", { url, name, max_pages: maxPages, max_depth: maxDepth });
      setUrl("");
      setName("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create website");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this website and all its ingested data?")) return;
    await api.delete(`/api/websites/${id}`);
    load();
  }

  async function handleReingest(id: number) {
    await api.post(`/api/websites/${id}/reingest`);
    load();
  }

  return (
    <div>
      <h1>Websites</h1>

      <form className="card onboarding-form" onSubmit={handleCreate}>
        <h3>Onboard a New Website</h3>
        <div className="form-row">
          <label>
            Website URL
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" required />
          </label>
          <label>
            Display Name
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Example Inc." required />
          </label>
        </div>
        <div className="form-row">
          <label>
            Max Pages
            <input
              type="number"
              min={1}
              value={maxPages}
              onChange={(e) => setMaxPages(Number(e.target.value))}
            />
          </label>
          <label>
            Max Depth
            <input
              type="number"
              min={0}
              value={maxDepth}
              onChange={(e) => setMaxDepth(Number(e.target.value))}
            />
          </label>
        </div>
        {error && <div className="error-text">{error}</div>}
        <button type="submit" disabled={creating}>
          {creating ? "Starting..." : "Start Ingestion"}
        </button>
      </form>

      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>URL</th>
            <th>Status</th>
            <th>Pages</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {websites.map((w) => (
            <tr key={w.id}>
              <td>
                <Link to={`/websites/${w.id}`}>{w.name}</Link>
              </td>
              <td className="muted">{w.url}</td>
              <td>
                <span className={`status-badge status-${w.status}`}>{STATUS_LABELS[w.status] ?? w.status}</span>
                {w.error_message && <div className="error-text">{w.error_message}</div>}
              </td>
              <td>{w.page_count}</td>
              <td className="actions-cell">
                <button onClick={() => handleReingest(w.id)}>Re-ingest</button>
                <button className="danger" onClick={() => handleDelete(w.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {websites.length === 0 && (
            <tr>
              <td colSpan={5} className="muted">
                No websites onboarded yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
