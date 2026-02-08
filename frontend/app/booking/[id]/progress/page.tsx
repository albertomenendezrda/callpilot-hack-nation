import ProgressClient from './ProgressClient';

export default async function ProgressPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProgressClient id={id} />;
}
