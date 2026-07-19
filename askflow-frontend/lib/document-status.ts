import { DocumentStatus } from "@/lib/types";

export const DOCUMENT_POLL_INTERVAL_MS = 3000;

export function isDocumentProcessing(status: DocumentStatus): boolean {
  return status === "processing";
}
