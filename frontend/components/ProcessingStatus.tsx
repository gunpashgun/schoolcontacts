"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { getJobStatus } from "@/lib/api";
import type { JobStatus } from "@/lib/api";

interface ProcessingStatusProps {
  jobId: string;
  onComplete: () => void;
}

export function ProcessingStatus({ jobId, onComplete }: ProcessingStatusProps) {
  const [status, setStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);
        setStatus(jobStatus);
        
        if (jobStatus.status === 'completed' || jobStatus.status === 'failed') {
          onComplete();
        }
      } catch (error) {
        console.error("Error fetching status:", error);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  if (!status) return <div>Loading...</div>;

  const progress = status.schools_count > 0 
    ? (status.processed_count / status.schools_count) * 100 
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Status</CardTitle>
        <CardDescription>Job ID: {jobId}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Badge variant={
            status.status === 'completed' ? 'default' :
            status.status === 'failed' ? 'destructive' :
            status.status === 'processing' ? 'secondary' : 'outline'
          }>
            {status.status}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {status.processed_count} / {status.schools_count} schools
          </span>
        </div>
        
        <Progress value={progress} />
        
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">Successful</div>
            <div className="text-2xl font-bold text-green-500">{status.successful_count}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Failed</div>
            <div className="text-2xl font-bold text-red-500">{status.failed_count}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Progress</div>
            <div className="text-2xl font-bold">{Math.round(progress)}%</div>
          </div>
        </div>
        
        {status.error_message && (
          <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
            {status.error_message}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

