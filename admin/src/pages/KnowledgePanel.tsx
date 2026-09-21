import { useState } from "react";
import { api } from "../api/client";
import type { KnowledgeQueryResult } from "../api/types";

export default function KnowledgePanel({ websiteId, websiteName }: { websiteId: string; websiteName: string }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<KnowledgeQueryResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await api.post<KnowledgeQueryResult>("/api/knowledge/query", {
        website_id: websiteId,
        website_name: websiteName,
        question,
      });
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h3>Test the Knowledge Base</h3>
      <form className="card" onSubmit={handleSubmit}>
        <label>
          Ask a question
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What services do you offer?" required />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>

      {result && (
        <div className="card">
          <h4>Answer</h4>
          <p style={{ whiteSpace: "pre-wrap" }}>{result.answer}</p>
          <h4>Retrieved Chunks</h4>
          {result.retrieved_chunks.map((chunk, i) => (
            <div key={i} className="chunk-preview">
              <div className="muted">
                {chunk.url} · similarity {chunk.similarity.toFixed(3)}
              </div>
              <p>{chunk.text.slice(0, 300)}...</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
