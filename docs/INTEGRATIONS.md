# 外部助手接入

在「我的 → 资料与工具 → 外部助手接入」创建接入凭据，选择授权范围，并下载味屿接入工具包。

工具包包含配方导入技能、Python 提交工具和 MCP 服务入口，可用于支持技能或 MCP 的外部助手。助手整理配方后提交到味屿，用户在导入记录中核对并保存。

## 内容格式

配方导入采用 `savorisle.recipe-import.v1` 格式，支持配方名称、说明、标签、分组材料与制作步骤。格式定义位于 [recipe-import.schema.json](../api/recipe-import.schema.json)。

## 连接与管理

接入工具使用味屿服务地址与页面生成的凭据。凭据由用户管理，可以在外部助手接入页面查看与撤销。

技能源码位于 [integrations/skills/savorisle-recipe-import](../integrations/skills/savorisle-recipe-import/SKILL.md)，接口定义位于 [openapi.json](../api/openapi.json)。
