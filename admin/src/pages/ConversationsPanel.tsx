import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Conversation, Message } from "../api/types";

export default function ConversationsPanel({ websiteId }: { websiteId: string }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [summary, setSummary] = useState<string | null>(null);
  const [summarizing, setSummarizing] = useState(false);

  useEffect(() => {
    api.get<Conversation[]>(`/api/conversations?website_id=${websiteId}`).then(setConversations);
  }, [websiteId]);

  async function openConversation(id: number) {
    setSelectedId(id);
    setSummary(null);
    const data = await api.get<{ conversation: Conversation; messages: Message[] }>(`/api/conversations/${id}`);
    setMessages(data.messages);
  }

  async function handleSummarize() {
    if (!selectedId) return;
    setSummarizing(true);
    try {
      const data = await api.get<{ summary: string }>(`/api/reporting/conversations/${selectedId}/summary`);
      setSummary(data.summary);
    } finally {
      setSummarizing(false);
    }
  }

  return (
    <div className="two-column">
      <div>
        <h3>Conversations</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Started</th>
            </tr>
          </thead>
          <tbody>
            {conversations.map((c) => (
              <tr key={c.id} className={selectedId === c.id ? "row-selected" : ""}>
                <td>
                  <button className="link-btn" onClick={() => openConversation(c.id)}>
                    #{c.id}
                  </button>
                </td>
                <td className="muted">{new Date(c.started_at).toLocaleString()}</td>
              </tr>
            ))}
            {conversations.length === 0 && (
              <tr>
                <td colSpan={2} className="muted">
                  No conversations yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedId && (
        <div className="card">
          <div className="panel-header">
            <h3>Conversation #{selectedId}</h3>
            <button onClick={handleSummarize} disabled={summarizing}>
              {summarizing ? "Summarizing..." : "Summarize"}
            </button>
          </div>
          {summary && <p className="summary-box">{summary}</p>}
          <div className="transcript">
            {messages.map((m) => (
              <div key={m.id} className={`bubble bubble-${m.role}`}>
                <div className="bubble-role">{m.role}</div>
                <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
