"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { FileUpload } from "@/components/file-upload";
import { ChatInterface } from "@/components/chat-interface";
import { FolderOpen } from "lucide-react";

const PdfViewer = dynamic(() => import("@/components/pdf-viewer").then((mod) => mod.PdfViewer), {
  ssr: false,
  loading: () => <div className="w-full h-full flex items-center justify-center text-muted-foreground bg-muted/5">Initializing PDF Engine...</div>,
});

export default function Home() {
  const [currentDoc, setCurrentDoc] = useState<any>(null);

  const handleUploadComplete = (data: any) => {
    console.log("Upload Complete:", data);
    setCurrentDoc(data);
  };

  return (
    <main className="h-screen w-full bg-background text-foreground flex flex-col">
      {/* Header */}
      <header className="h-14 border-b flex items-center px-6 gap-2 shrink-0">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
          AF
        </div>
        <h1 className="font-semibold text-lg">AskFlow</h1>
        {currentDoc && (
          <div className="ml-8 flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 px-3 py-1 rounded-full">
            <FolderOpen className="w-4 h-4" />
            <span>{currentDoc.filename}</span>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {!currentDoc ? (
          // Empty State: Upload
          <div className="h-full flex flex-col items-center justify-center p-8 animate-in fade-in duration-500">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold tracking-tight mb-2">
                Chat with your Documents
              </h2>
              <p className="text-muted-foreground max-w-lg mx-auto">
                Upload a PDF to get started. Ask questions, extract summaries, and see exact citations.
              </p>
            </div>
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        ) : (
          // Split View
          <div className="h-full flex divide-x">
            <div className="w-1/2 bg-muted/5 relative">
              <PdfViewer url={`http://127.0.0.1:8000/api/v1/documents/${currentDoc.id}/pdf`} />
            </div>
            <div className="w-1/2 bg-background flex flex-col">
              <ChatInterface documentId={currentDoc.id} />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
