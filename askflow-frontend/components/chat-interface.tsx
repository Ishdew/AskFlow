"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
// import axios from "axios"; // Will use in next step

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations?: any[];
}

interface ChatInterfaceProps {
    documentId: number;
}

export function ChatInterface({ documentId }: ChatInterfaceProps) {
    // Silence unused variable warning for now by logging it
    useEffect(() => {
        console.log("Chat initialized for document:", documentId);
    }, [documentId]);

    const [messages, setMessages] = useState<Message[]>([
        {
            id: "welcome",
            role: "assistant",
            content: "Hello! I've read your document. Ask me anything about it.",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

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
            // SIMULATION: Mock response for now to test UI
            await new Promise(resolve => setTimeout(resolve, 1000));

            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "I am a placeholder AI. The RAG backend is coming next! 🧠"
            }

            setMessages((prev) => [...prev, aiMessage]);

        } catch (error) {
            console.error("Chat error", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
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
                            <div className={cn(
                                "relative px-4 py-3 rounded-2xl max-w-[80%] text-sm leading-relaxed shadow-sm",
                                msg.role === "user"
                                    ? "bg-primary text-primary-foreground rounded-tr-sm"
                                    : "bg-muted border border-border rounded-tl-sm text-foreground"
                            )}>
                                {msg.content}
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
            </div>

            {/* Input Area */}
            <div className="p-4 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
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
