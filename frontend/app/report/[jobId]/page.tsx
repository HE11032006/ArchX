import { ReportView } from "@/features/report";
import { mockReport } from "@/shared/data/mockReport";

interface ReportPageProps {
  searchParams: Promise<{ repo?: string }>;
}

export default async function ReportPage({ searchParams }: ReportPageProps) {
  const { repo } = await searchParams;

  return <ReportView report={mockReport} repoUrl={repo} />;
}
