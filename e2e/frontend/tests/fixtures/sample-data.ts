export const testUsers = {
  valid: {
    username: 'test_user',
    password: 'Test1234',
    email: 'test@example.com',
  },
  invalid: {
    shortPassword: 'Test1',
    noUppercase: 'test1234',
    noDigit: 'TestPassword',
  },
};

export const testHotel = {
  name_cn: '测试酒店',
  brand: 'atour',
  province: '上海市',
  city: '上海市',
  address_cn: '浦东新区世纪大道100号',
};

export const testTranslation = {
  zhToEn: {
    text: '酒店提供免费WiFi和停车场',
    source_lang: 'zh-CN',
    target_lang: 'en-US',
  },
};
