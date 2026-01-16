import { NextRequest, NextResponse } from 'next/server';
import { getJob, supabase } from '@/lib/server/supabase';

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const format = request.nextUrl.searchParams.get('format') || 'csv';
    const job = await getJob(params.jobId);

    if (!job || job.status !== 'completed') {
      return NextResponse.json(
        { error: 'Job not found or not completed' },
        { status: 404 }
      );
    }

    // Get results from Supabase
    const { data: schools } = await supabase
      .from('school_results')
      .select('*')
      .eq('job_id', params.jobId);

    const { data: personLeads } = await supabase
      .from('person_leads')
      .select('*')
      .eq('job_id', params.jobId);

    if (format === 'csv') {
      // Generate CSV
      const headers = [
        'School Name', 'Type', 'Location', 'Foundation', 'NPSN',
        'Website', 'Email', 'WhatsApp', 'Quality Score', 'Decision Makers'
      ];
      
      const rows = (schools || []).map((school: any) => [
        school.school_name || '',
        school.school_type || '',
        school.location || '',
        school.foundation_name || '',
        school.npsn || '',
        school.official_website || '',
        school.official_email || '',
        school.whatsapp_business || '',
        (school.data_quality_score || 0).toString(),
        Array.isArray(school.decision_makers) ? school.decision_makers.length : 0
      ]);

      const csv = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n');

      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="leads_${params.jobId}.csv"`,
        },
      });
    } else if (format === 'json') {
      return NextResponse.json({
        job_id: params.jobId,
        schools: schools || [],
        person_leads: personLeads || [],
      });
    }

    return NextResponse.json({ error: 'Unsupported format' }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

