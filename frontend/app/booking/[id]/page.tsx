import BookingClient from './BookingClient';

export default async function BookingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <BookingClient id={id} />;
}
