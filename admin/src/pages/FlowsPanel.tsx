import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Flow, FlowStep } from "../api/types";

const STEP_TYPES = ["show_options", "retrieve_information", "ask_followup", "collect_input", "call_action"];

export default function FlowsPanel({ websiteId }: { websiteId: string }) {
  const [flows, setFlows] = useState<Flow[]>([]);
  const [selected, setSelected] = useState<Flow | null>(null);
  const [discovering, setDiscovering] = useState(false);

  function load() {
    api.get<Flow[]>(`/api/flows?website_id=${websiteId}`).then(setFlows);
  }

  useEffect(load, [websiteId]);

  async function handleDiscover() {
    setDiscovering(true);
    try {
      await api.post("/api/flows/discover", { website_id: websiteId });
      load();
    } finally {
      setDiscovering(false);
    }
  }

  async function togglePublish(flow: Flow) {
    await api.post(`/api/flows/${flow.id}/${flow.published ? "unpublish" : "publish"}`);
    load();
  }

  async function handleRename(flow: Flow) {
    const name = prompt("New flow name", flow.flow_name);
    if (!name) return;
    await api.patch(`/api/flows/${flow.id}`, { flow_name: name });
    load();
  }

  async function handleDelete(flow: Flow) {
    if (!confirm(`Delete flow "${flow.flow_name}"?`)) return;
    await api.delete(`/api/flows/${flow.id}`);
    setSelected(null);
    load();
  }

  async function handleAddStep(flow: Flow) {
    const type = prompt(`Step type (${STEP_TYPES.join(", ")})`, "ask_followup");
    if (!type || !STEP_TYPES.includes(type)) return;
    const optionsText = prompt("Options (comma-separated, optional)", "");
    const options = (optionsText || "").split(",").map((o) => o.trim()).filter(Boolean);
    await api.post(`/api/flows/${flow.id}/steps`, { type, options });
    load();
    refreshSelected(flow.id);
  }

  async function handleRemoveStep(flow: Flow, index: number) {
    await api.delete(`/api/flows/${flow.id}/steps/${index}`);
    load();
    refreshSelected(flow.id);
  }

  async function refreshSelected(flowId: number) {
    const updated = await api.get<Flow>(`/api/flows/${flowId}`);
    setSelected(updated);
  }

  return (
    <div className="two-column">
      <div>
        <div className="panel-header">
          <h3>Flows</h3>
          <button onClick={handleDiscover} disabled={discovering}>
            {discovering ? "Discovering..." : "Re-run Discovery"}
          </button>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Published</th>
              <th>Steps</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {flows.map((f) => (
              <tr key={f.id} className={selected?.id === f.id ? "row-selected" : ""}>
                <td>
                  <button className="link-btn" onClick={() => setSelected(f)}>
                    {f.flow_name}
                  </button>
                </td>
                <td>{f.published ? "✅" : "—"}</td>
                <td>{f.steps.length}</td>
                <td className="actions-cell">
                  <button onClick={() => togglePublish(f)}>{f.published ? "Unpublish" : "Publish"}</button>
                  <button onClick={() => handleRename(f)}>Rename</button>
                  <button className="danger" onClick={() => handleDelete(f)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {flows.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  No flows yet. Click "Re-run Discovery" once the website is ready.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selected && (
        <div className="card">
          <h3>{selected.flow_name}</h3>
          <p className="muted">Triggers: {selected.trigger.join(", ") || "none"}</p>
          <ol className="step-list">
            {selected.steps.map((step: FlowStep, i: number) => (
              <li key={i}>
                <strong>{step.type}</strong>
                {step.options.length > 0 && <span> — {step.options.join(", ")}</span>}
                <button className="link-btn danger" onClick={() => handleRemoveStep(selected, i)}>
                  remove
                </button>
              </li>
            ))}
          </ol>
          <button onClick={() => handleAddStep(selected)}>+ Add Step</button>
        </div>
      )}
    </div>
  );
}
