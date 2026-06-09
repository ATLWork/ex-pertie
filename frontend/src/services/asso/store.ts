import { makeAutoObservable } from 'mobx';

export interface AssoUserInfoDTO {
  userId?: string;
  userName?: string;
  realName?: string;
  mobile?: string;
  email?: string;
  avatar?: string;
  tenantId?: string;
  tenantName?: string;
  [key: string]: unknown;
}

class UserStore {
  assoToken: string = typeof window !== 'undefined' ? (localStorage.getItem('assoToken') ?? '') : '';
  userInfo: AssoUserInfoDTO = (() => {
    if (typeof window === 'undefined') return {};
    try {
      return JSON.parse(localStorage.getItem('userInfo') ?? '{}');
    } catch {
      return {};
    }
  })();
  permissionList: string[] = (() => {
    if (typeof window === 'undefined') return [];
    try {
      return JSON.parse(localStorage.getItem('permissions') ?? '[]');
    } catch {
      return [];
    }
  })();
  isAuth: boolean = false;

  constructor() {
    makeAutoObservable(this);
  }

  setToken(token: string) {
    this.assoToken = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('assoToken', token);
    }
  }

  getToken(): string {
    return this.assoToken || (typeof window !== 'undefined' ? localStorage.getItem('assoToken') || '' : '');
  }

  setUserInfo(info: AssoUserInfoDTO) {
    this.userInfo = info;
    if (typeof window !== 'undefined') {
      localStorage.setItem('userInfo', JSON.stringify(info));
    }
  }

  setPermissions(list: string[]) {
    this.permissionList = list;
    if (typeof window !== 'undefined') {
      localStorage.setItem('permissions', JSON.stringify(list));
    }
  }

  setIsAuth(val: boolean) {
    this.isAuth = val;
  }

  clear() {
    this.assoToken = '';
    this.userInfo = {};
    this.permissionList = [];
    this.isAuth = false;
    if (typeof window !== 'undefined') {
      localStorage.clear();
    }
  }
}

export const userStore = new UserStore();

export const isInFeishu = (): boolean => {
  if (typeof window === 'undefined') return false;
  return /聘眼/.test(navigator.userAgent) || (window as any).__LARK_IPFS_ENV__ !== undefined;
};