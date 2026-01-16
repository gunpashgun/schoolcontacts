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
    // Import and call the enrichment service
    const { processSchoolsBackground } = await import('@/lib/server/enrichment');
    processSchoolsBackground(jobId, schools).catch(console.error);

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

