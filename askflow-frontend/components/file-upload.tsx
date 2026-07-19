"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import axios from "axios";
import { cn } from "@/lib/utils";
import { API_BASE_URL } from "@/lib/config";

interface FileUploadProps {
    onUploadComplete: (data: any) => void;
}

export function FileUpload({ onUploadComplete }: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleUpload(e.dataTransfer.files[0]);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            handleUpload(e.target.files[0]);
        }
    };

    const handleUpload = async (file: File) => {
        if (file.type !== "application/pdf") {
            setError("Only PDF files are allowed.");
            return;
        }

        setIsUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            // Direct call to backend
            const response = await axios.post(`${API_BASE_URL}/documents/upload`, formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            onUploadComplete(response.data);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to upload document.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="w-full max-w-md mx-auto">
            <motion.div
                layout
                className={cn(
                    "relative border-2 border-dashed rounded-xl p-10 transition-all duration-200 ease-in-out text-center cursor-pointer overflow-hidden",
                    isDragging
                        ? "border-blue-500 bg-blue-50/10"
                        : "border-muted-foreground/25 hover:border-muted-foreground/50 hover:bg-muted/30"
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileSelect}
                />

                <AnimatePresence mode="wait">
                    {isUploading ? (
                        <motion.div
                            key="uploading"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="flex flex-col items-center gap-4"
                        >
                            <div className="relative">
                                <div className="w-16 h-16 rounded-full border-4 border-muted/30 animate-spin border-t-blue-500" />
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <FileText className="w-6 h-6 text-muted-foreground" />
                                </div>
                            </div>
                            <p className="text-sm font-medium animate-pulse">Uploading...</p>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="idle"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="flex flex-col items-center gap-4"
                        >
                            <div className={cn(
                                "p-4 rounded-full transition-colors",
                                isDragging ? "bg-blue-100 text-blue-600" : "bg-muted text-foreground"
                            )}>
                                <Upload className="w-8 h-8" />
                            </div>
                            <div>
                                <p className="text-lg font-semibold">Drop your PDF here</p>
                                <p className="text-sm text-muted-foreground mt-1">or click to browse</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Success/Error Overlay */}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-4 p-3 rounded-lg bg-red-500/10 text-red-500 text-sm flex items-center gap-2 justify-center"
                    >
                        <AlertCircle className="w-4 h-4" />
                        {error}
                    </motion.div>
                )}
            </motion.div>

            <div className="mt-4 text-center">
                <p className="text-xs text-muted-foreground">
                    Supported: PDF (Text-selectable)
                </p>
            </div>
        </div>
    );
}
