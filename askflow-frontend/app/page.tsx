"use client";

import { useRouter } from "next/navigation";
import { FileUpload } from "@/components/file-upload";

export default function Home() {
  const router = useRouter();

  const handleUploadComplete = (data: any) => {
    router.push(`/documents/${data.id}`);
  };

  return (
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
  );
}
