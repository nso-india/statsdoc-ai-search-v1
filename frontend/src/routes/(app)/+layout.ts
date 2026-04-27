import type { LayoutLoad } from './$types';
import { user } from '$lib/stores';
import { get } from 'svelte/store';
import { browser } from '$app/environment';

export const load: LayoutLoad = async () => {
  // Only get user data on client-side where stores are available
  if (browser) {
    const currentUser = get(user);
    console.log('Layout load - current user:', currentUser);
    return {
      user: currentUser
    };
  }
  
  return {
    user: undefined
  };
};
