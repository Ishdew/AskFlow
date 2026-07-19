"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import axios from "axios";
import { FolderOpen, Loader2, AlertCircle } from "lucide-react";
import { ChatInterface } from "@/components/chat-interface";
import { ActiveCitation, DocumentDetail, DocumentStatus } from "@/lib/types";
import { API_BASE_URL } from "@/lib/config";
import { DOCUMENT_POLL_INTERVAL_MS } from "@/lib/document-status";

const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((mod) => mod.PdfViewer), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-muted-foreground bg-muted/5">Initializing PDF Engine...</div>,
});

export default function DocumentPage() {
  const { id } = useParams<{ id: string }>();
  const primaryDocumentId = Number(id);

  const [filename, setFilename] = useState<string | null>(null);
  const [status, setStatus] = useState<DocumentStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(() => Number.isNaN(primaryDocumentId));
  const [activeCitation, setActiveCitation] = useState<ActiveCitation | null>(null);

  // Render-time guard, not useEffect: Next's router can restore a previously
  // mounted instance for a revisited document instead of remounting fresh, so
  // plain useState defaults aren't guaranteed to reset just by navigating
  // away and back to the same document id. Consolidates all "reset when the
  // route's document id changes" state in one place.
  const [syncedPrimaryId, setSyncedPrimaryId] = useState(primaryDocumentId);
  if (primaryDocumentId !== syncedPrimaryId) {
    setSyncedPrimaryId(primaryDocumentId);
    setActiveCitation(null);
    setFilename(null);
    setStatus(null);
    setErrorMessage(null);
    setNotFound(Number.isNaN(primaryDocumentId));
  }

  useEffect(() => {
    if (Number.isNaN(primaryDocumentId)) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    // Self-reschedules while status is "processing", so this page reflects a
    // background job finishing without a page refresh. Extends the same
    // single fetch this page already needed for the header filename, rather
    // than introducing a third fetch mechanism.
    async function fetchAndMaybeReschedule() {
      try {
        const res = await axios.get<DocumentDetail>(`${API_BASE_URL}/documents/${primaryDocumentId}`);
        if (cancelled) return;
        setFilename(res.data.filename);
        setStatus(res.data.status);
        setErrorMessage(res.data.error_message);
        if (res.data.status === "processing") {
          timer = setTimeout(fetchAndMaybeReschedule, DOCUMENT_POLL_INTERVAL_MS);
        }
      } catch (err) {
        if (cancelled) return;
        // Only an actual 404 means "not found" - any other error (a
        // transient blip) keeps polling instead of permanently showing
        // "not found" for a document that's still there.
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          setNotFound(true);
          return;
        }
        timer = setTimeout(fetchAndMaybeReschedule, DOCUMENT_POLL_INTERVAL_MS);
      }
    }

    fetchAndMaybeReschedule();
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [primaryDocumentId]);

  if (notFound) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 text-center p-8">
        <p className="text-lg font-medium">Document not found</p>
        <p className="text-sm text-muted-foreground max-w-sm">
          It may have been deleted. Pick another document from the sidebar or upload a new one.
        </p>
      </div>
    );
  }

  // Swapping which PDF is displayed (e.g. clicking a citation from a
  // non-primary document) never changes what the chat itself is scoped to.
  const displayedDocumentId = activeCitation?.documentId ?? primaryDocumentId;

  return (
    <div className="h-full flex flex-col">
      {filename && (
        <div className="h-10 border-b flex items-center px-4 gap-2 shrink-0 text-sm text-muted-foreground bg-muted/20">
          <FolderOpen className="w-4 h-4" />
          <span>{filename}</span>
        </div>
      )}
      <div className="flex-1 flex divide-x overflow-hidden">
        <div className="w-1/2 bg-muted/5 relative">
          <PdfViewer
            url={`${API_BASE_URL}/documents/${displayedDocumentId}/pdf`}
            activeCitation={activeCitation}
          />
        </div>
        <div className="w-1/2 bg-background flex flex-col">
          {status === "processing" ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              <p className="text-sm font-medium">Still processing this document…</p>
              <p className="text-xs text-muted-foreground max-w-xs">
                The PDF is ready to view on the left. Chat unlocks once indexing finishes.
              </p>
            </div>
          ) : status === "failed" ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-8">
              <AlertCircle className="w-6 h-6 text-red-500" />
              <p className="text-sm font-medium">Processing failed</p>
              <p className="text-xs text-muted-foreground max-w-xs">
                {errorMessage ?? "Something went wrong while indexing this document."}
              </p>
            </div>
          ) : (
            <ChatInterface documentId={primaryDocumentId} onCitationClick={setActiveCitation} />
          )}
        </div>
      </div>
    </div>
  );
}
