import request from './axios';
import { getFsAppId } from './constant';
import type { AssoUserInfoDTO } from './store';

export interface LoginByFeiShuResult {
  assoToken: string;
  system?: string;
  tenants?: unknown[];
}

export async function loginByFeiShu(code: string): Promise<LoginByFeiShuResult> {
  const fsAppId = getFsAppId();
  const res = await request.post('/asso/loginByFeiShu', {
    code,
    appId: fsAppId,
  });
  return res.data.data;
}

export async function getUserByToken(assoToken?: string): Promise<AssoUserInfoDTO> {
  const res = await request.post('/api/asso/asso/getUserByToken', assoToken ? { assoToken, source: 'unknown' } : { source: 'unknown' });
  return res.data.data;
}