"use client";

import { useState } from "react";
import { InputForm } from "@/components/InputForm";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getJobResults, downloadResults } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [processing, setProcessing] = useState(true);

  const handleProcess = (id: string) => {
    setJobId(id);
    setProcessing(true);
    setResults(null);
  };

  const handleComplete = async () => {
    setProcessing(false);
    if (jobId) {
      try {
        const data = await getJobResults(jobId);
        setResults(data);
      } catch (error) {
        console.error("Error fetching results:", error);
      }
    }
  };

  const handleDownload = async (format: string) => {
    if (!jobId) return;
    try {
      const blob = await downloadResults(jobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads_${jobId}.${format}`;
      a.click();
    } catch (error) {
      console.error("Error downloading:", error);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-bold mb-2">Indonesia EdTech Lead Gen</h1>
          <p className="text-muted-foreground">
            Enrich school contacts with decision makers and verified WhatsApp/Email
          </p>
        </div>

        {!jobId && <InputForm onProcess={handleProcess} />}

        {jobId && processing && (
          <ProcessingStatus jobId={jobId} onComplete={handleComplete} />
        )}

        {results && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Results</CardTitle>
                  <CardDescription>
                    {results.successful} successful, {results.failed} failed
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => handleDownload('csv')}>
                    Download CSV
                  </Button>
                  <Button variant="outline" onClick={() => handleDownload('excel')}>
                    Download Excel
                  </Button>
                  <Button variant="outline" onClick={() => handleDownload('json')}>
                    Download JSON
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>School Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Decision Makers</TableHead>
                    <TableHead>Verified</TableHead>
                    <TableHead>Quality</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.schools?.map((school: any, idx: number) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{school.school_name}</TableCell>
                      <TableCell>{school.school_type}</TableCell>
                      <TableCell>{school.location}</TableCell>
                      <TableCell>{school.decision_makers_count}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{school.verified_contacts}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={school.data_quality_score > 0.7 ? "default" : "outline"}>
                          {Math.round(school.data_quality_score * 100)}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
