import { redirect } from 'next/navigation';

/**
 * Call history is now part of Active Tasks.
 * Redirect /dashboard/history to /dashboard/tasks.
 */
export default function HistoryPage() {
  redirect('/dashboard/tasks');
}
