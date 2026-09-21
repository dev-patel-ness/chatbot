import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { FaqTopic, ReportingSummary, SafetyEvent } from "../api/types";

export default function ReportingPanel({ websiteId }: { websiteId: string }) {
  const [summary, setSummary] = useState<ReportingSummary | null>(null);
  const [faqs, setFaqs] = useState<FaqTopic[] | null>(null);
  const [loadingFaqs, setLoadingFaqs] = useState(false);
  const [safetyEvents, setSafetyEvents] = useState<SafetyEvent[]>([]);

  useEffect(() => {
    api.get<ReportingSummary>(`/api/reporting/summary?website_id=${websiteId}`).then(setSummary);
    api.get<SafetyEvent[]>("/api/reporting/safety-events").then(setSafetyEvents);
  }, [websiteId]);

  async function handleLoadFaqs() {
    setLoadingFaqs(true);
    try {
      const data = await api.get<{ top_topics: FaqTopic[] }>(`/api/reporting/faqs?website_id=${websiteId}`);
      setFaqs(data.top_topics);
    } finally {
      setLoadingFaqs(false);
    }
  }

  return (
    <div>
      <h3>Reporting</h3>
      {summary && (
        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-value">{summary.total_conversations}</div>
            <div className="stat-label">Conversations</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.total_messages}</div>
            <div className="stat-label">Messages</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.average_messages_per_conversation}</div>
            <div className="stat-label">Avg Msgs/Conversation</div>
          </div>
        </div>
      )}

      <div className="two-column">
        <div className="card">
          <h4>Most-Used Flows</h4>
          <ul>
            {summary?.most_used_flows.map((f) => (
              <li key={f.flow_name}>
                {f.flow_name} — {f.uses}
              </li>
            ))}
            {summary?.most_used_flows.length === 0 && <li className="muted">None yet</li>}
          </ul>
        </div>
        <div className="card">
          <h4>Most-Used Tools/Actions</h4>
          <ul>
            {summary?.most_used_tools.map((t) => (
              <li key={t.tool_name}>
                {t.tool_name} — {t.uses}
              </li>
            ))}
            {summary?.most_used_tools.length === 0 && <li className="muted">None yet</li>}
          </ul>
        </div>
      </div>

      <div className="card">
        <div className="panel-header">
          <h4>Frequently Asked Topics</h4>
          <button onClick={handleLoadFaqs} disabled={loadingFaqs}>
            {loadingFaqs ? "Analyzing..." : "Analyze FAQs"}
          </button>
        </div>
        {faqs && (
          <ul>
            {faqs.map((f, i) => (
              <li key={i}>
                <strong>{f.topic}</strong> (~{f.count_estimate}) — {f.example_phrasings.join(" / ")}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="card">
        <h4>Safety Events (all websites)</h4>
        <table className="data-table">
          <thead>
            <tr>
              <th>Direction</th>
              <th>Message</th>
              <th>Reason</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {safetyEvents.map((e) => (
              <tr key={e.id}>
                <td>{e.direction}</td>
                <td>{e.message.slice(0, 80)}</td>
                <td className="muted">{e.reason}</td>
                <td className="muted">{new Date(e.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {safetyEvents.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No safety events logged.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
