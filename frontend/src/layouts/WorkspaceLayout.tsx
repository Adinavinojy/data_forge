import { ReactNode } from 'react';

interface WorkspaceLayoutProps {
  sidebar: ReactNode;
  preview: ReactNode;
  log: ReactNode;
  header: ReactNode;
}

export function WorkspaceLayout({ sidebar, preview, log, header }: WorkspaceLayoutProps) {
  return (
    <div className="flex flex-col h-screen w-full bg-[#121212] overflow-hidden font-sans text-gray-300">
      {/* Header */}
      <div className="h-12 border-b border-black flex items-center px-4 pl-20 shrink-0 bg-[#2d2d2d] z-20 shadow-md electron-draggable">
        {header}
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="shrink-0 z-10 h-full">
          {sidebar}
        </div>

        {/* Right Side: Preview + Log */}
        <div className="flex flex-col flex-1 min-w-0 h-full relative">
          {/* Preview Panel */}
          <div className="flex-1 min-h-0 relative bg-[#1e1e1e]">
            {preview}
          </div>

          {/* Log Panel */}
          <div className="shrink-0 z-10 border-t border-black shadow-[0_-2px_10px_rgba(0,0,0,0.3)]">
            {log}
          </div>
        </div>
      </div>
    </div>
  );
}
