"use client";

import { DocumentSidebar } from "@/components/document-sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen w-full bg-background text-foreground flex flex-col">
      <header className="h-14 border-b flex items-center px-6 gap-2 shrink-0">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
          AF
        </div>
        <h1 className="font-semibold text-lg">AskFlow</h1>
      </header>
      <div className="flex-1 flex overflow-hidden">
        <DocumentSidebar />
        <div className="flex-1 overflow-hidden relative">
          {children}
        </div>
      </div>
    </div>
  );
}
