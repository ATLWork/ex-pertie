Feature: 完整业务链路测试
  描述：模拟真实用户完整操作流程，验证端到端链路正确性
  Background:
    Given 系统运行正常，运营人员账号test@example.com已注册

  @P0
  Scenario: 运营人员完整操作链路
    When 运营人员打开系统登录页，输入账号test@example.com，密码Test123456登录成功
    And 进入数据导入页面，上传测试酒店数据文件，确认导入
    And 进入术语管理页，添加术语"酒店"-"Hotel"
    And 进入翻译管理页，全选所有数据，执行批量翻译
    And 进入导出页面，全选所有数据，选择Expedia模板格式导出
    Then 成功下载Excel文件，文件内容正确，格式符合Expedia要求
