"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import axios from "axios";
import { FileText, Trash2, ChevronLeft, ChevronRight, Inbox, Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/config";
import { useDocuments } from "@/lib/use-documents";

export function DocumentSidebar() {
  const { id } = useParams<{ id: string }>();
  const activeId = id ? Number(id) : null;
  const router = useRouter();
  const { documents, isLoading, refresh } = useDocuments();
  const [collapsed, setCollapsed] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function handleDelete(docId: number, e: React.MouseEvent) {
    e.stopPropagation();
    if (!window.confirm("Delete this document? This cannot be undone.")) return;

    setDeletingId(docId);
    try {
      await axios.delete(`${API_BASE_URL}/documents/${docId}`);
      await refresh();
      if (docId === activeId) {
        router.push("/");
      }
    } catch (err) {
      console.error("Failed to delete document", err);
    } finally {
      setDeletingId(null);
    }
  }

  if (collapsed) {
    return (
      <div className="w-10 border-r shrink-0 flex flex-col items-center py-3">
        <button
          onClick={() => setCollapsed(false)}
          className="p-1.5 hover:bg-muted rounded-full transition-colors"
          title="Show documents"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-64 border-r shrink-0 flex flex-col bg-muted/5">
      <div className="h-10 flex items-center justify-between px-3 border-b shrink-0">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Documents
        </span>
        <button
          onClick={() => setCollapsed(true)}
          className="p-1 hover:bg-muted rounded-full transition-colors"
          title="Hide documents"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading ? (
          <p className="text-xs text-muted-foreground p-2">Loading...</p>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center text-center gap-2 p-4 text-muted-foreground">
            <Inbox className="w-6 h-6" />
            <p className="text-xs">No documents yet</p>
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.id}
              onClick={() => router.push(`/documents/${doc.id}`)}
              title={new Date(doc.upload_date).toLocaleString()}
              className={cn(
                "w-full text-left px-2.5 py-2 rounded-lg text-sm flex items-start gap-2 group transition-colors cursor-pointer",
                doc.id === activeId
                  ? "bg-blue-600 text-white"
                  : "hover:bg-muted text-foreground"
              )}
            >
              {doc.status === "processing" ? (
                <Loader2 className="w-4 h-4 mt-0.5 shrink-0 animate-spin" />
              ) : doc.status === "failed" ? (
                <AlertCircle className={cn("w-4 h-4 mt-0.5 shrink-0", doc.id === activeId ? "text-white" : "text-red-500")} />
              ) : (
                <FileText className="w-4 h-4 mt-0.5 shrink-0" />
              )}
              <span className="flex-1 min-w-0">
                <span className="block truncate">{doc.filename}</span>
                <span
                  title={doc.status === "failed" ? (doc.error_message ?? undefined) : undefined}
                  className={cn(
                    "block text-[10px]",
                    doc.status === "failed"
                      ? (doc.id === activeId ? "text-white/90" : "text-red-500")
                      : (doc.id === activeId ? "text-white/70" : "text-muted-foreground")
                  )}
                >
                  {doc.status === "processing" ? "Processing…"
                    : doc.status === "failed" ? "Processing failed"
                    : `${doc.chunk_count} chunks`}
                </span>
              </span>
              <button
                onClick={(e) => handleDelete(doc.id, e)}
                disabled={deletingId === doc.id}
                className={cn(
                  "p-1 rounded-full shrink-0 opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-100",
                  doc.id === activeId ? "hover:bg-white/20" : "hover:bg-red-500/10 hover:text-red-500"
                )}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
