Feature: 酒店数据导入
  描述：验证酒店/房间数据文件上传、解析、校验、导入全流程功能
  Background:
    Given 系统运行正常，用户已使用admin账号登录

  @P0
  Scenario: 正常导入Excel格式酒店数据
    When 用户进入"数据导入"页面
    And 选择标准有效Excel文件上传
    Then 文件上传成功，系统解析完成后显示数据预览
    When 用户点击"确认导入"按钮
    Then 数据导入成功，提示导入成功信息
    And 酒店列表页显示导入的数据

  @P1
  Scenario Outline: 异常文件导入测试
    When 用户进入"数据导入"页面
    And 选择文件 "<文件名>" 上传
    Then 导入失败，显示错误提示 "<预期错误>"

    Examples:
      | 文件名                     | 预期错误                                                     |
      | empty_file.xlsx            | 文件内容为空，请上传包含有效酒店数据的文件                     |
      | invalid_format.docx        | 文件格式不支持，请上传.xlsx/.xls/.csv格式的文件               |
      | missing_required_field.xlsx| 缺失必填字段"酒店名称"，请修正后重新上传                       |
