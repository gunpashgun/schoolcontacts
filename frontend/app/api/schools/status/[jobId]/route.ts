import { NextRequest, NextResponse } from 'next/server';
import { getJob } from '@/lib/server/supabase';

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const job = await getJob(params.jobId);

    if (!job) {
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      job_id: job.id,
      status: job.status,
      schools_count: job.schools_count,
      processed_count: job.processed_count,
      successful_count: job.successful_count,
      failed_count: job.failed_count,
      created_at: job.created_at,
      completed_at: job.completed_at,
      error_message: job.error_message,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

