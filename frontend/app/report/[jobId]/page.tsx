import { ReportPageClient } from "@/features/report/components/report-page-client";

interface ReportPageProps {
  params: Promise<{ jobId: string }>;
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { jobId } = await params;
  return <ReportPageClient jobId={jobId} />;
}
