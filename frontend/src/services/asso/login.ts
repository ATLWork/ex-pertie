import { getGateway, getSsoBase, getFsAppId } from './constant';
import { isInFeishu } from './store';

/**
 * 飞书静默授权
 * 重定向到 gateway loginByFeiShu 接口，由后端完成 code 换 token 并回跳业务页
 */
const jmlLogin = (): string => {
  const gateway = getGateway();
  const fsAppId = getFsAppId();
  const redirectUri = `${gateway}/api/asso/login/loginByFeiShu?system=ATOS&redirectUri=${encodeURIComponent(window.location.href)}&appId=${fsAppId}`;
  return `https://open.feishu.cn/open-apis/authen/v1/authorize?app_id=${fsAppId}&redirect_uri=${encodeURIComponent(redirectUri)}`;
};

const goToLogin = () => {
  const ssoBase = getSsoBase();
  const { origin, pathname, search, hash } = window.location;
  const current = encodeURIComponent(`${origin}${pathname}${search}${hash}`);
  const target = `${ssoBase}/login?redirect_uri=${current}`;
  window.location.href = target;
};

export const login = () => ({
  jmlLogin,
  goToLogin: () => {
    if (isInFeishu()) {
      window.location.href = jmlLogin();
    } else {
      goToLogin();
    }
  },
});