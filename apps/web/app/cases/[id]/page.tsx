import CaseDetailContent from "@/cases/CaseDetailContent";

type Props = {
  params: { id: string };
};

export default function CaseDetailPage({ params }: Props) {
  return <CaseDetailContent caseId={params.id} />;
}
