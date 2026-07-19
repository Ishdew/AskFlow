export interface CitationBox {
  x0: number;
  x1: number;
  top: number;
  bottom: number;
}

export interface Citation {
  id: number;
  document_id: number;
  page: number;
  text: string;
  score: number | null;
  bounding_box: CitationBox[] | null;
}

export interface ActiveCitation {
  chunkId: number;
  documentId: number;
  page: number;
  boundingBox: CitationBox[] | null;
}

export type SearchMode = "vector" | "keyword" | "hybrid";

export type DocumentStatus = "processing" | "ready" | "failed";

// Named DocumentSummary (not Document) to avoid colliding with the DOM's
// global `Document` type and react-pdf's own `Document` component.
export interface DocumentSummary {
  id: number;
  filename: string;
  upload_date: string;
  chunk_count: number;
  status: DocumentStatus;
  error_message: string | null;
}

export interface DocumentDetail {
  id: number;
  filename: string;
  upload_date: string;
  status: DocumentStatus;
  error_message: string | null;
}

// Distinct from chat-interface.tsx's local `Message` (which uses a string id
// for locally-generated optimistic messages before any round trip).
export interface ConversationMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface ConversationResponse {
  id: number | null;
  messages: ConversationMessage[];
}
