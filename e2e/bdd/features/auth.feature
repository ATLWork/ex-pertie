Feature: 用户身份认证
  描述：验证系统登录、权限校验、退出登录等身份相关功能
  Background:
    Given 系统服务运行正常
    And 测试数据库已初始化，存在以下账号：
      | 邮箱                  | 密码          | 用户名       | 角色       |
      | admin@example.com     | Admin123456   | Admin User   | 超级管理员 |
      | test@example.com      | Test123456    | Test User    | 运营人员   |
      | viewer@example.com    | Viewer123456  | Viewer User  | 只读用户   |

  @P0
  Scenario: 管理员账号正常登录成功
    When 用户访问系统登录页
    And 输入邮箱 "admin@example.com"，密码 "Admin123456"
    And 点击登录按钮
    Then 系统登录成功，跳转至首页
    And 页面顶部显示欢迎信息包含 "Admin User"

  @P0
  Scenario: 普通用户正常登录成功
    When 用户访问系统登录页
    And 输入邮箱 "test@example.com"，密码 "Test123456"
    And 点击登录按钮
    Then 系统登录成功，跳转至首页

  @P1
  Scenario Outline: 登录异常场景测试
    When 用户访问系统登录页
    And 输入邮箱 "<邮箱>"，密码 "<密码>"
    And 点击登录按钮
    Then 登录失败，页面显示错误提示 "<预期错误提示>"

    Examples:
      | 邮箱                  | 密码             | 预期错误提示                               |
      | test@example.com      | WrongPass123     | 用户名或密码错误，请重试                     |
      | notexist@test.com     | Test123456       | 该账号不存在，请先注册                       |
      | <empty>               | Test123456       | 请输入邮箱地址                               |
      | test@example.com      | <empty>          | 请输入密码                                   |

  @P1
  Scenario: 正常退出登录
    Given 用户已使用admin账号登录系统
    When 用户点击右上角"退出登录"按钮
    Then 系统成功退出，跳转至登录页
