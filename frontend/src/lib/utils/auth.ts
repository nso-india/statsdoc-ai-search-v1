import { redirect } from '@sveltejs/kit';
import type { SessionUser } from '$lib/stores';

/**
 * Check if user has admin privileges
 */
export function requireAdmin(user: SessionUser | undefined): void {
  console.log('requireAdmin check:', { user, role: user?.role, is_superuser: user?.is_superuser });
  
  if (!user) {
    console.log('No user found, redirecting to chat');
    throw redirect(302, '/chat');
  }
  
  if (user.role !== 'admin' && !user.is_superuser) {
    console.log('User is not admin, redirecting to chat');
    throw redirect(302, '/chat');
  }
  
  console.log('User is admin, allowing access');
}

/**
 * Load function helper for admin-only pages
 */
export async function adminOnlyLoad(parent: () => Promise<{ user?: SessionUser }>) {
  const { user } = await parent();
  requireAdmin(user);
  return { user };
}
