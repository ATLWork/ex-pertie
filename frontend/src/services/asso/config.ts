// Configuration for anonymous access
// When ANONYMOUS_ENABLED=true, users can access without login

// Check if anonymous mode is enabled
// Check env variable FIRST, then localStorage override
export const isAnonymousEnabled = (): boolean => {
  if (typeof window === 'undefined') return false;

  // Check localStorage override first (runtime override)
  const stored = localStorage.getItem('anonymous_mode');
  if (stored === 'true') return true;
  if (stored === 'false') return false;

  // Check env variable - this is the primary source
  if ((window as any).__ENV__?.NEXT_PUBLIC_ANONYMOUS_ENABLED === 'true') return true;
  if ((window as any).__NEXT_PUBLIC_ANONYMOUS_ENABLED === 'true') return true;
  if (process.env.NEXT_PUBLIC_ANONYMOUS_ENABLED === 'true') return true;

  return false;
};

// Legacy export - defaults to false for module compatibility
export const ANONYMOUS_ENABLED = false;

export const ANONYMOUS_USER = {
  id: 0,
  username: 'anonymous',
  email: 'anonymous@local',
  fullName: 'Anonymous User',
  created_at: '',
};

// Enable anonymous mode at runtime
export const enableAnonymousMode = () => {
  localStorage.setItem('anonymous_mode', 'true');
};

// Disable anonymous mode
export const disableAnonymousMode = () => {
  localStorage.setItem('anonymous_mode', 'false');
};