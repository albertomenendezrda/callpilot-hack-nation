import SuccessClient from './SuccessClient';

export default async function SuccessPage({ params }: { params: Promise<{ id: string }> }) {
  // Success page doesn't need the id, but we need to await params for Next.js 15
  await params;
  return <SuccessClient />;
}
