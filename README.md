# zentao-cli

面向禅道开源版 21.7.5 的 Python 命令行客户端。

首版目标是覆盖产品经理和个人日常协作里的高频命令：

- 自动或交互式登录
- 产品只读：查询、查看
- 任务处理：查询、查看、更新状态、评论、完成
- Bug 只读：查询、查看
- 需求处理：查询、查看、创建、变更标题/描述/验收标准
- 默认表格输出，支持 `--json` 供脚本解析

> 当前实现基于禅道 RESTful API v1，默认请求路径形如
> `<zentao-url>/api.php/v1/...`。如果禅道部署在子路径下，请填写禅道根地址，例如
> `https://example.com/zentao`。

## 安装

开发模式安装：

```bash
git clone https://github.com/JBpeople/zentao-cli.git
cd zentao-cli
python -m pip install -e ".[dev]"
```

验证安装：

```bash
zentao --version
zentao --help
```

也可以直接运行模块：

```bash
python -m zentao_cli.main --help
```

## 登录

推荐把本地凭据放在 `.env`，这样 token 过期时 CLI 会自动重新登录：

```env
ZENTAO_URL=https://zentao.example.com
ZENTAO_USERNAME=alice
ZENTAO_PASSWORD=secret
```

`.env` 已加入 `.gitignore`，不要提交到 GitHub。

配置好 `.env` 后可以直接运行命令：

```bash
zentao product list
zentao bug list --product 5
```

也可以手动登录：

```bash
zentao login
```

手动登录会提示输入 URL、账号和密码，并保存会话 token，不保存明文密码。

查看当前登录账号：

```bash
zentao whoami
```

本地 session 配置由 `platformdirs` 决定保存位置。Windows 上通常在：

```text
C:\Users\<you>\AppData\Local\zentao-cli\config.toml
```

## 产品命令

查看当前账号可见的产品列表：

```bash
zentao product list
zentao product list --json
```

查看产品详情：

```bash
zentao product view 5
zentao product view 5 --json
```

建议先用 `product list` 找到产品 ID，再查询该产品下的 Bug 或需求：

```bash
zentao product list
zentao bug list --product 5
zentao story list --product 5
```

## 任务命令

任务列表需要执行 ID。可以先从禅道网页确认执行 ID，再查询任务。

查看某个执行下分配给自己的任务：

```bash
zentao task list --execution 303 --mine
```

按状态筛选：

```bash
zentao task list --execution 303 --mine --status doing
zentao task list --execution 303 --status wait
zentao task list --execution 303 --status done
```

查看任务详情：

```bash
zentao task view 123
```

更新任务状态：

```bash
zentao task update 123 --status doing
```

给任务添加评论：

```bash
zentao task comment 123 "已经完成本地验证，等待联调"
```

完成任务：

```bash
zentao task finish 123 --comment "功能已完成，测试通过"
```

## Bug 命令

Bug 列表必须指定产品 ID：

```bash
zentao bug list --product 5
```

查询分配给某个账号的 Bug：

```bash
zentao bug list --product 5 --assigned-to alice
```

按状态筛选：

```bash
zentao bug list --product 5 --status active
```

查看 Bug 详情：

```bash
zentao bug view 456
zentao bug view 456 --json
```

如果指定的产品 ID 不存在，或当前账号不可见，CLI 会报错而不是使用禅道接口的默认回退结果。

## 需求命令

需求列表必须指定产品 ID：

```bash
zentao story list --product 5
```

按状态筛选：

```bash
zentao story list --product 5 --status active
```

查看需求详情：

```bash
zentao story view 789
zentao story view 789 --json
```

创建需求：

```bash
zentao story create --product 5 --title "支持批量导入客户" --spec "作为运营，我希望批量导入客户，以减少手工录入。" --verify "上传模板文件后，系统创建客户并返回导入结果。"
```

常用可选参数：

```bash
zentao story create --product 5 --title "支持批量导入客户" --spec "需求描述" --verify "验收标准" --pri 2 --category feature --json
```

变更需求标题、描述或验收标准：

```bash
zentao story change 789 --title "支持 Excel 批量导入客户" --spec "更新后的需求描述" --verify "更新后的验收标准"
zentao story change 789 --title "支持 Excel 批量导入客户" --spec "更新后的需求描述" --json
```

`story create` 会先校验 `--product` 是否存在且当前账号可见，避免禅道接口在产品 ID 错误时回退到默认产品。

如果指定的产品 ID 不存在，或当前账号不可见，CLI 会报错而不是使用禅道接口的默认回退结果。

## JSON 输出

查询类命令支持 `--json`，适合自动化脚本。

```bash
zentao product list --json
zentao task list --execution 303 --mine --json
zentao task view 123 --json
zentao bug list --product 5 --assigned-to alice --json
zentao story list --product 5 --json
zentao story create --product 5 --title "支持批量导入客户" --spec "需求描述" --json
zentao story change 789 --title "新标题" --spec "新描述" --json
```

成功输出结构：

```json
{
  "ok": true,
  "data": []
}
```

错误输出结构：

```json
{
  "ok": false,
  "error": {
    "type": "AuthError",
    "message": "not logged in"
  }
}
```

PowerShell 中保存结果：

```powershell
zentao task list --execution 303 --mine --json > tasks.json
```

配合 `jq`：

```bash
zentao bug list --product 5 --json | jq ".data[] | {id, title, status}"
```

## 常见工作流

每天开始工作：

```bash
zentao product list
zentao task list --execution 303 --mine
zentao bug list --product 5 --assigned-to alice --status active
```

开始处理任务：

```bash
zentao task update 123 --status doing
zentao task comment 123 "开始处理"
```

完成任务：

```bash
zentao task finish 123 --comment "已提交并自测通过"
```

导出脚本输入：

```bash
zentao product list --json > products.json
zentao task list --execution 303 --mine --json > tasks.json
zentao story list --product 5 --json > stories.json
```

产品经理创建并调整需求：

```bash
zentao product list
zentao story create --product 5 --title "支持批量导入客户" --spec "作为运营，我希望批量导入客户，以减少手工录入。" --verify "上传模板文件后，系统创建客户并返回导入结果。" --pri 2
zentao story change 789 --title "支持 Excel 批量导入客户" --spec "补充字段映射和错误行下载规则" --verify "导入后能看到成功数、失败数和失败明细"
zentao story view 789
```

## 手动 Smoke Test

连接真实禅道开源版 21.7.5 后，建议按顺序验证：

```bash
zentao product list
zentao product view 5 --json
zentao bug list --product 5 --json
zentao story list --product 5 --json
zentao task list --execution 303 --json
```

如果 `task list --execution 303` 返回权限或上下文错误，请确认该执行 ID 对当前账号可见。

验证写操作前，请先使用测试任务：

```bash
zentao task update 123 --status doing
zentao task comment 123 "CLI smoke test"
zentao task finish 123 --comment "CLI smoke test done"
```

验证需求写操作前，请先确认一个可以创建测试数据的产品 ID，并使用明显的测试标题：

```bash
zentao story create --product 5 --title "[CLI TEST] 创建需求 smoke test" --spec "CLI smoke test" --verify "CLI smoke test" --json
zentao story change 789 --title "[CLI TEST] 更新需求 smoke test" --spec "CLI smoke test updated" --verify "CLI smoke test updated" --json
```

## 开发

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行测试：

```bash
pytest -v
```

当前测试不依赖真实禅道服务，HTTP 请求通过 mock 覆盖。

项目结构：

```text
zentao_cli/
  main.py              # Typer 入口
  config.py            # 本地配置和 .env 读取
  auth.py              # 登录、自动登录和 profile 加载
  client.py            # Zentao API v1 HTTP client
  models.py            # Product/Task/Bug/Story 等归一化模型
  formatters.py        # JSON 输出和表格辅助
  errors.py            # 用户可见异常
  commands/
    product.py
    task.py
    bug.py
    story.py
```

## 当前限制

- 只面向禅道开源版 21.7.5 的 API v1。
- 产品和 Bug 目前只支持只读查询。
- 需求支持创建和变更标题/描述/验收标准，暂不支持关闭、评审、拆分、指派或状态流转。
- Bug 和需求列表必须传 `--product`。
- 任务列表必须传 `--execution`。
- 当前没有 `logout`、多 profile 和 keyring 存储。
- `task update/comment/finish` 会直接修改禅道数据，请先在测试任务上验证。
- `story create/change` 会直接修改禅道数据，请先在测试产品上验证。
