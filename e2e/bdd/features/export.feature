Feature: Expedia模板导出
  描述：验证Expedia格式Excel模板生成和下载功能
  Background:
    Given 系统运行正常，用户已使用admin账号登录
    And 系统已存在已完成翻译的酒店数据

  @P0
  Scenario: 导出全部酒店数据
    When 用户进入"导出管理"页面
    And 选择"全选"所有数据
    And 选择导出格式为"Expedia标准模板"
    And 点击"导出"按钮
    Then 系统开始生成文件，5秒内文件生成完成自动下载
    And 下载文件名为"Expedia酒店数据_"开头的xlsx文件
