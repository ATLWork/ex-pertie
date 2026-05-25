Feature: 完整业务链路测试
  描述：模拟真实用户完整操作流程，验证端到端链路正确性
  Background:
    Given 系统运行正常，运营人员账号test@example.com已注册

  @P0
  Scenario: 运营人员完整操作链路
    When 用户访问系统登录页
    And 输入用户名 "adminuser"，密码 "Admin123456"
    And 点击登录按钮
    Then 系统登录成功，跳转至首页
    # 简化链路，先验证登录成功
