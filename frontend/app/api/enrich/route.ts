/**
 * Proxy route to Vercel Python serverless function
 * This calls the Python function at /api/enrich.py
 */
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Call Vercel Python function
    // In Vercel, Python functions are accessible at /api/enrich
    const pythonFunctionUrl = process.env.VERCEL_URL 
      ? `https://${process.env.VERCEL_URL}/api/enrich`
      : 'http://localhost:3000/api/enrich';
    
    // For local development, we need to handle this differently
    // In production on Vercel, Python functions are automatically available
    if (process.env.NODE_ENV === 'development') {
      // In dev, we can't easily call Python functions
      // Return a message that processing will happen in production
      return NextResponse.json({
        message: 'Python enrichment will run in production on Vercel',
        job_id: body.job_id,
      });
    }
    
    // In production, Vercel handles Python functions automatically
    // We'll use a workaround: call it via internal API
    const response = await fetch(pythonFunctionUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`Python function error: ${response.statusText}`);
    }
    
    return NextResponse.json(await response.json());
  } catch (error: any) {
    console.error('Enrich proxy error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

