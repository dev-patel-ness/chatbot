import { API_BASE_URL } from "../api/client";

export default function EmbedPanel({ websiteId, websiteName }: { websiteId: string; websiteName: string }) {
  const snippet = `<script src="${API_BASE_URL}/widget/chatbot.js"></script>
<script>
  Chatbot.init({
    websiteId: "${websiteId}",
    websiteName: "${websiteName}",
    apiBaseUrl: "${API_BASE_URL}",
  });
</script>`;

  function copy() {
    navigator.clipboard.writeText(snippet);
  }

  return (
    <div>
      <h3>Embed Code</h3>
      <p className="muted">Paste this snippet before the closing &lt;/body&gt; tag of the target website.</p>
      <pre className="code-block">{snippet}</pre>
      <button onClick={copy}>Copy to clipboard</button>
    </div>
  );
}
