"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { Send, User, Loader2, Sparkles, FileText, Layers, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import { ActiveCitation, Citation, ConversationResponse, SearchMode } from "@/lib/types";
import { API_BASE_URL } from "@/lib/config";
import { useDocuments } from "@/lib/use-documents";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations?: Citation[];
}

interface ChatInterfaceProps {
    documentId: number;
    onCitationClick?: (citation: ActiveCitation) => void;
}

const SEARCH_MODES: { value: SearchMode; label: string }[] = [
    { value: "vector", label: "Vector" },
    { value: "keyword", label: "Keyword" },
    { value: "hybrid", label: "Hybrid" },
];

const WELCOME_MESSAGE: Message = {
    id: "welcome",
    role: "assistant",
    content: "Hello! I've read your document. Ask me anything about it.",
};

function truncateFilename(name: string, max = 20) {
    return name.length > max ? name.slice(0, max - 1) + "…" : name;
}

export function ChatInterface({ documentId, onCitationClick }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [historyStatus, setHistoryStatus] = useState<"loading" | "ready">("loading");
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isClearing, setIsClearing] = useState(false);
    const [searchMode, setSearchMode] = useState<SearchMode>("hybrid");
    const [extraDocIds, setExtraDocIds] = useState<number[]>([]);
    const [pickerOpen, setPickerOpen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const { documents } = useDocuments();

    // Reset per-document state whenever the primary document changes -
    // render-time sync (not useEffect) for the same lint-rule reason as the
    // citation-jump logic in pdf-viewer.tsx. Clearing `messages` here (rather
    // than only in the fetch effect below) is what stops a previous
    // document's conversation from flashing on screen during the navigation.
    const [syncedDocId, setSyncedDocId] = useState(documentId);
    if (documentId !== syncedDocId) {
        setSyncedDocId(documentId);
        setExtraDocIds([]);
        setMessages([]);
        setHistoryStatus("loading");
    }

    // Load this document's persisted conversation on mount and whenever the
    // document changes. Falls back to the welcome message only once we know
    // for sure there's no history yet (empty response), not before.
    useEffect(() => {
        let cancelled = false;
        setHistoryStatus("loading");
        axios.get<ConversationResponse>(`${API_BASE_URL}/documents/${documentId}/conversation`)
            .then((res) => {
                if (cancelled) return;
                const loaded: Message[] = res.data.messages.map((m) => ({
                    id: String(m.id),
                    role: m.role,
                    content: m.content,
                    citations: m.citations ?? undefined,
                }));
                setMessages(loaded.length > 0 ? loaded : [WELCOME_MESSAGE]);
            })
            .catch(() => {
                if (!cancelled) setMessages([WELCOME_MESSAGE]);
            })
            .finally(() => {
                if (!cancelled) setHistoryStatus("ready");
            });
        return () => { cancelled = true; };
    }, [documentId]);

    const documentIds = useMemo(
        () => Array.from(new Set([documentId, ...extraDocIds])),
        [documentId, extraDocIds]
    );
    const otherDocuments = documents.filter((d) => d.id !== documentId);

    function toggleExtraDoc(id: number) {
        setExtraDocIds((prev) =>
            prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
        );
    }

    function filenameForDocId(docId: number): string | undefined {
        return documents.find((d) => d.id === docId)?.filename;
    }

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await axios.post(`${API_BASE_URL}/chat/query`, {
                message: input,
                document_ids: documentIds,
                primary_document_id: documentId,
                search_mode: searchMode
            });

            const data = response.data;

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: data.answer,
                citations: data.citations
            };

            setMessages((prev) => [...prev, aiMessage]);

        } catch (error) {
            console.error("Chat error", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "Sorry, I encountered an error while processing your request."
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    async function handleClearConversation() {
        if (!window.confirm("Clear this conversation? This cannot be undone.")) return;
        setIsClearing(true);
        try {
            await axios.delete(`${API_BASE_URL}/documents/${documentId}/conversation`);
            setMessages([WELCOME_MESSAGE]);
        } catch (error) {
            console.error("Failed to clear conversation", error);
        } finally {
            setIsClearing(false);
        }
    }

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
                {historyStatus === "loading" ? (
                    <div className="h-full flex items-center justify-center">
                        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                <>
                <AnimatePresence initial={false}>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={cn(
                                "flex w-full gap-3",
                                msg.role === "user" ? "flex-row-reverse" : "flex-row"
                            )}
                        >
                            {/* Avatar */}
                            <div className={cn(
                                "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                                msg.role === "assistant" ? "bg-blue-600 text-white" : "bg-muted text-muted-foreground"
                            )}>
                                {msg.role === "assistant" ? <Sparkles className="w-5 h-5" /> : <User className="w-5 h-5" />}
                            </div>

                            {/* Bubble */}
                            <div className="flex flex-col gap-2 max-w-[80%]">
                                <div className={cn(
                                    "relative px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm",
                                    msg.role === "user"
                                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                                        : "bg-muted border border-border rounded-tl-sm text-foreground"
                                )}>
                                    {msg.content}
                                </div>

                                {msg.citations && msg.citations.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5">
                                        {msg.citations.map((citation) => {
                                            const isOtherDoc = citation.document_id !== documentId;
                                            const otherFilename = isOtherDoc ? filenameForDocId(citation.document_id) : undefined;
                                            return (
                                                <button
                                                    key={citation.id}
                                                    onClick={() => onCitationClick?.({
                                                        chunkId: citation.id,
                                                        documentId: citation.document_id,
                                                        page: citation.page,
                                                        boundingBox: citation.bounding_box,
                                                    })}
                                                    className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-muted/70 border border-border hover:border-blue-500 hover:text-blue-500 transition-colors"
                                                    title={citation.text}
                                                >
                                                    <FileText className="w-3 h-3" />
                                                    {otherFilename
                                                        ? `${truncateFilename(otherFilename)} · p.${citation.page}`
                                                        : `Page ${citation.page}`}
                                                </button>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex gap-3"
                    >
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white">
                            <Loader2 className="w-5 h-5 animate-spin" />
                        </div>
                        <div className="bg-muted border border-border px-4 py-3 rounded-2xl rounded-tl-sm">
                            <span className="animate-pulse text-muted-foreground text-sm">Thinking...</span>
                        </div>
                    </motion.div>
                )}
                </>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="flex items-center justify-center gap-2 mb-3">
                    <div className="flex items-center gap-1 bg-muted/50 border border-border rounded-full p-1">
                        {SEARCH_MODES.map((m) => (
                            <button
                                key={m.value}
                                type="button"
                                onClick={() => setSearchMode(m.value)}
                                className={cn(
                                    "text-xs px-3 py-1 rounded-full transition-colors",
                                    searchMode === m.value
                                        ? "bg-blue-600 text-white"
                                        : "text-muted-foreground hover:text-foreground"
                                )}
                            >
                                {m.label}
                            </button>
                        ))}
                    </div>

                    {otherDocuments.length > 0 && (
                        <div className="relative">
                            <button
                                type="button"
                                onClick={() => setPickerOpen((v) => !v)}
                                className={cn(
                                    "flex items-center gap-1 text-xs px-3 py-1.5 rounded-full border transition-colors",
                                    extraDocIds.length > 0
                                        ? "bg-blue-600 text-white border-blue-600"
                                        : "bg-muted/50 border-border text-muted-foreground hover:text-foreground"
                                )}
                            >
                                <Layers className="w-3.5 h-3.5" />
                                {extraDocIds.length > 0 ? `+${extraDocIds.length} doc${extraDocIds.length > 1 ? "s" : ""}` : "Add documents"}
                            </button>

                            <AnimatePresence>
                                {pickerOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 8 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 8 }}
                                        className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-56 bg-background border border-border rounded-xl shadow-lg p-2 space-y-1 z-20"
                                    >
                                        <p className="text-[10px] uppercase tracking-wide text-muted-foreground px-2 pb-1">
                                            Also search in
                                        </p>
                                        {otherDocuments.map((doc) => (
                                            <label
                                                key={doc.id}
                                                className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-muted cursor-pointer text-xs"
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={extraDocIds.includes(doc.id)}
                                                    onChange={() => toggleExtraDoc(doc.id)}
                                                    className="accent-blue-600"
                                                />
                                                <span className="truncate flex-1">{doc.filename}</span>
                                            </label>
                                        ))}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}

                    <button
                        type="button"
                        onClick={handleClearConversation}
                        disabled={isClearing || historyStatus === "loading"}
                        title="Clear conversation"
                        className="flex items-center justify-center p-1.5 rounded-full border border-border text-muted-foreground bg-muted/50 hover:text-red-500 hover:border-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {isClearing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="flex items-center gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question..."
                        className="flex-1 bg-muted/50 border border-border focus:border-blue-500 rounded-full px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-muted-foreground/70"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm shrink-0 flex items-center justify-center relative"
                    >
                        <div className={cn("transition-all flex items-center", isLoading ? "scale-0 w-0 opacity-0" : "scale-100 w-auto opacity-100")}>
                            <Send className="w-4 h-4 ml-0.5" />
                        </div>
                        {isLoading && <Loader2 className="w-4 h-4 animate-spin absolute" />}
                    </button>
                </form>
                <div className="text-center mt-2">
                    <p className="text-[10px] text-muted-foreground">AI can make mistakes. Verify important information.</p>
                </div>
            </div>
        </div>
    );
}
