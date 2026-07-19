"use client";

import { useEffect, useState, useCallback } from "react";
import { usePathname } from "next/navigation";
import axios from "axios";
import { API_BASE_URL } from "@/lib/config";
import { DocumentSummary } from "@/lib/types";
import { DOCUMENT_POLL_INTERVAL_MS, isDocumentProcessing } from "@/lib/document-status";

export function useDocuments() {
  const pathname = usePathname();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  // Tracks which pathname's fetch has completed - isLoading is derived by
  // comparing this to the current pathname (render-time) rather than a
  // separate flag set synchronously in the effect body.
  const [loadedForPathname, setLoadedForPathname] = useState<string | null>(null);

  useEffect(() => {
    // Re-fetch whenever the route changes (covers uploads, which always end in
    // a navigation to /documents/{id}). Deletes update local state directly
    // via refresh() below instead of relying on this effect. Self-reschedules
    // (setTimeout, not setInterval) while any document is still "processing",
    // so the sidebar picks up status transitions without a shared store -
    // stops on its own once nothing is left processing.
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function fetchAndMaybeReschedule() {
      try {
        const res = await axios.get<DocumentSummary[]>(`${API_BASE_URL}/documents`);
        if (cancelled) return;
        setDocuments(res.data);
        setLoadedForPathname(pathname);
        if (res.data.some((d) => isDocumentProcessing(d.status))) {
          timer = setTimeout(fetchAndMaybeReschedule, DOCUMENT_POLL_INTERVAL_MS);
        }
      } catch {
        // Transient failure - keep the loop alive rather than dying on one
        // hiccup; a poll that gives up after one bad request isn't a poll.
        if (!cancelled) timer = setTimeout(fetchAndMaybeReschedule, DOCUMENT_POLL_INTERVAL_MS);
      }
    }

    fetchAndMaybeReschedule();
    return () => { cancelled = true; if (timer) clearTimeout(timer); };
  }, [pathname]);

  const refresh = useCallback(async () => {
    const res = await axios.get<DocumentSummary[]>(`${API_BASE_URL}/documents`);
    setDocuments(res.data);
  }, []);

  return { documents, isLoading: loadedForPathname !== pathname, refresh };
}
