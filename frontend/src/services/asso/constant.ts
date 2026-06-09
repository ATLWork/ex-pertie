// Lazy-loaded environment variables to avoid SSR/build-time issues

const DEFAULT_GATEWAY = 'https://gateway.corp.yaduo.com';
const DEFAULT_SSO_BASE = 'https://atos.yaduo.com';
const DEFAULT_FS_APP_ID = 'cli_a7b9f08db57ad00d';

let _gateway: string = DEFAULT_GATEWAY;
let _ssoBase: string = DEFAULT_SSO_BASE;
let _fsAppId: string = DEFAULT_FS_APP_ID;

export const getGateway = (): string => {
  if (_gateway === DEFAULT_GATEWAY) {
    _gateway = typeof window !== 'undefined'
      ? ((window as any).__ENV__?.NEXT_PUBLIC_GATEWAY
      || (window as any).__NEXT_PUBLIC_GATEWAY
      || process.env.NEXT_PUBLIC_GATEWAY) ?? DEFAULT_GATEWAY
      : DEFAULT_GATEWAY;
  }
  return _gateway;
};

export const getSsoBase = (): string => {
  if (_ssoBase === DEFAULT_SSO_BASE) {
    _ssoBase = typeof window !== 'undefined'
      ? ((window as any).__ENV__?.NEXT_PUBLIC_SSO_BASE
      || (window as any).__NEXT_PUBLIC_SSO_BASE
      || process.env.NEXT_PUBLIC_SSO_BASE) ?? DEFAULT_SSO_BASE
      : DEFAULT_SSO_BASE;
  }
  return _ssoBase;
};

export const getFsAppId = (): string => {
  if (_fsAppId === DEFAULT_FS_APP_ID) {
    _fsAppId = typeof window !== 'undefined'
      ? ((window as any).__ENV__?.NEXT_PUBLIC_FS_APP_ID
      || (window as any).__NEXT_PUBLIC_FS_APP_ID
      || process.env.NEXT_PUBLIC_FS_APP_ID) ?? DEFAULT_FS_APP_ID
      : DEFAULT_FS_APP_ID;
  }
  return _fsAppId;
};

// Re-export as constants for backward compatibility (evaluated lazily)
export const NEXT_PUBLIC_GATEWAY = getGateway();
export const NEXT_PUBLIC_SSO_BASE = getSsoBase();
export const NEXT_PUBLIC_FS_APP_ID = getFsAppId();

export const GATEWAY = NEXT_PUBLIC_GATEWAY;
export const SSO_BASE = NEXT_PUBLIC_SSO_BASE;
export const FS_APP_ID = NEXT_PUBLIC_FS_APP_ID;