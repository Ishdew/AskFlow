"use client";

import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, RotateCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface PdfViewerProps {
    url: string;
}

export function PdfViewer({ url }: PdfViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState<number>(1.0);
    const [rotation, setRotation] = useState<number>(0);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    return (
        <div className="flex flex-col h-full bg-muted/10 w-full relative">
            {/* Premium Floating Toolbar */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
                <motion.div
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="flex items-center gap-2 bg-background/80 backdrop-blur-md border border-border/50 shadow-lg rounded-full px-4 py-2"
                >
                    <button
                        onClick={() => setPageNumber(p => Math.max(1, p - 1))}
                        disabled={pageNumber <= 1}
                        className="p-1.5 hover:bg-muted rounded-full disabled:opacity-50 transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>

                    <span className="text-sm font-medium tabular-nums min-w-[3rem] text-center select-none">
                        {pageNumber} / {numPages || "--"}
                    </span>

                    <button
                        onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}
                        disabled={pageNumber >= numPages}
                        className="p-1.5 hover:bg-muted rounded-full disabled:opacity-50 transition-colors"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>

                    <div className="w-px h-4 bg-border/50 mx-1" />

                    <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} className="p-1.5 hover:bg-muted rounded-full">
                        <ZoomOut className="w-4 h-4" />
                    </button>
                    <span className="text-xs tabular-nums text-muted-foreground w-8 text-center">{Math.round(scale * 100)}%</span>
                    <button onClick={() => setScale(s => Math.min(2.0, s + 0.1))} className="p-1.5 hover:bg-muted rounded-full">
                        <ZoomIn className="w-4 h-4" />
                    </button>
                </motion.div>
            </div>

            {/* Scrollable PDF Area */}
            <div className="flex-1 overflow-auto flex justify-center p-8">
                <div className="shadow-2xl ring-1 ring-black/5 dark:ring-white/5 bg-white">
                    <Document
                        file={url}
                        onLoadSuccess={onDocumentLoadSuccess}
                        loading={
                            <div className="flex items-center justify-center h-96 w-64">
                                <div className="w-8 h-8 border-4 border-muted/30 border-t-blue-500 rounded-full animate-spin" />
                            </div>
                        }
                        error={
                            <div className="flex items-center justify-center h-96 w-64 text-red-500 text-sm p-4 text-center">
                                Failed to load PDF.
                            </div>
                        }
                    >
                        <Page
                            pageNumber={pageNumber}
                            scale={scale}
                            rotate={rotation}
                            className="max-w-full"
                            renderAnnotationLayer={true}
                            renderTextLayer={true}
                        />
                    </Document>
                </div>
            </div>
        </div>
    );
}
