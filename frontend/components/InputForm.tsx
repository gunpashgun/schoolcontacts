"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { processSchools, processSchoolsFile } from "@/lib/api";

interface InputFormProps {
  onProcess: (jobId: string) => void;
}

export function InputForm({ onProcess }: InputFormProps) {
  const [textInput, setTextInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return;
    
    setLoading(true);
    try {
      const response = await processSchools({
        schools: textInput,
        format: "text",
      });
      onProcess(response.job_id);
    } catch (error) {
      console.error("Error processing schools:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSubmit = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      const format = file.name.endsWith('.csv') ? 'csv' : 
                    file.name.endsWith('.json') ? 'json' : 
                    (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) ? 'excel' : 'text';
      
      const response = await processSchoolsFile(file, format);
      onProcess(response.job_id);
    } catch (error) {
      console.error("Error processing file:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Input Schools</CardTitle>
        <CardDescription>
          Enter schools in text format or upload a file (CSV, JSON, Excel)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="text">
          <TabsList>
            <TabsTrigger value="text">Text Input</TabsTrigger>
            <TabsTrigger value="file">File Upload</TabsTrigger>
          </TabsList>
          
          <TabsContent value="text" className="space-y-4">
            <Textarea
              placeholder="PPPK Petra - Private Christian (Elementary to High School, Education Board/Group)&#10;Yohanes Gabriel Foundation - Private Catholic (Elementary to High School, Religious Foundation)"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={10}
              className="font-mono"
            />
            <Button 
              onClick={handleTextSubmit} 
              disabled={!textInput.trim() || loading}
              className="w-full"
            >
              {loading ? "Processing..." : "Process Schools"}
            </Button>
          </TabsContent>
          
          <TabsContent value="file" className="space-y-4">
            <input
              type="file"
              accept=".csv,.json,.xlsx,.xls,.txt"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full"
            />
            <Button 
              onClick={handleFileSubmit} 
              disabled={!file || loading}
              className="w-full"
            >
              {loading ? "Processing..." : "Upload & Process"}
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

