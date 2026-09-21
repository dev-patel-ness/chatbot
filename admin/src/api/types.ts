export interface Website {
  id: number;
  website_id: string;
  url: string;
  name: string;
  max_pages: number;
  max_depth: number;
  status: string;
  error_message: string | null;
  page_count: number;
  created_at: string;
  updated_at: string;
}

export interface FlowStep {
  type: string;
  options: string[];
}

export interface Flow {
  id: number;
  website_id: string;
  flow_name: string;
  trigger: string[];
  steps: FlowStep[];
  published: boolean;
}

export interface Conversation {
  id: number;
  website_id: string;
  started_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface ReportingSummary {
  total_conversations: number;
  total_messages: number;
  average_messages_per_conversation: number;
  most_used_flows: { flow_name: string; uses: number }[];
  most_used_tools: { tool_name: string; uses: number }[];
}

export interface FaqTopic {
  topic: string;
  example_phrasings: string[];
  count_estimate: number;
}

export interface SafetyEvent {
  id: number;
  conversation_id: number | null;
  direction: string;
  message: string;
  reason: string | null;
  created_at: string;
}

export interface KnowledgeChunkPreview {
  text: string;
  url: string;
  page_title: string;
  section: string;
  content_type: string;
  website_id: string;
  similarity: number;
}

export interface KnowledgeQueryResult {
  answer: string;
  sources: string[];
  retrieved_chunks: KnowledgeChunkPreview[];
}
