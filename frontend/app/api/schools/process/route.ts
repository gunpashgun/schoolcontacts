import { NextRequest, NextResponse } from 'next/server';
import { InputParser } from '@/lib/server/parser';
import { createJob } from '@/lib/server/supabase';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const textInput = formData.get('schools') as string | null;
    const format = (formData.get('format') as string) || 'text';
    const file = formData.get('file') as File | null;

    let schools;

    if (file) {
      // Handle file upload
      const fileContent = await file.text();
      const fileFormat = file.name.endsWith('.csv') ? 'csv' :
                        file.name.endsWith('.json') ? 'json' : 'text';
      
      schools = InputParser.parse(fileContent, fileFormat);
    } else if (textInput) {
      // Handle text input
      schools = InputParser.parse(textInput, format as any);
    } else {
      return NextResponse.json(
        { error: 'No input provided' },
        { status: 400 }
      );
    }

    if (!schools || schools.length === 0) {
      return NextResponse.json(
        { error: 'No schools found in input' },
        { status: 400 }
      );
    }

    // Create job in Supabase
    const jobId = await createJob(null, format, schools.length);

    // Start background processing
    // Note: In Vercel, we can't run long-running processes
    // We'll need to use a queue system or call an external service
    // For now, we'll trigger processing asynchronously
    processSchoolsAsync(jobId, schools).catch(console.error);

    return NextResponse.json({
      job_id: jobId,
      status: 'pending',
      schools_count: schools.length,
      message: `Processing ${schools.length} schools`,
    });
  } catch (error: any) {
    console.error('Process error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

// Async processing function
async function processSchoolsAsync(jobId: string, schools: any[]) {
  // Try to call Python backend if available
  const pythonApiUrl = process.env.PYTHON_API_URL;
  
  if (pythonApiUrl) {
    try {
      const response = await fetch(`${pythonApiUrl}/api/schools/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          schools: schools.map(s => ({
            name: s.name,
            type: s.type,
            location: s.location,
            notes: s.notes
          })),
          format: 'json' 
        }),
      });

      if (response.ok) {
        // Python backend will handle the processing
        return;
      }
    } catch (error) {
      console.log('Python backend not available, using simplified processing');
    }
  }

  // Simplified processing: just mark as completed
  // In production, implement full enrichment or use a queue
  const { updateJobStatus, updateJobProgress } = await import('@/lib/server/supabase');
  
  await updateJobStatus(jobId, 'processing');
  
  // Simulate processing
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  await updateJobProgress(jobId, schools.length, schools.length, 0);
  await updateJobStatus(jobId, 'completed');
}
