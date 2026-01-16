"use client";

import { Button } from "@/components/ui/button";
import { downloadResults } from "@/lib/api";

interface DownloadButtonProps {
  jobId: string;
  format: 'csv' | 'excel' | 'json';
  children: React.ReactNode;
}

export function DownloadButton({ jobId, format, children }: DownloadButtonProps) {
  const handleDownload = async () => {
    try {
      const blob = await downloadResults(jobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads_${jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download error:", error);
      alert("Failed to download results");
    }
  };

  return (
    <Button variant="outline" onClick={handleDownload}>
      {children}
    </Button>
  );
}

