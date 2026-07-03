# zentao-cli

基于禅道 API v1 和少量经典接口实现的 Python 命令行客户端。

首版目标是覆盖产品经理和个人日常协作里的高频命令：

- 自动或交互式登录
- 产品只读：查询、查看
- 项目只读：查询、查看
- 执行只读：查询、查看
- 任务处理：查询、查看、创建、更新、删除、评论、完成
- Bug 处理：查询、查看、创建、更新、删除
- 需求处理：查询、查看、创建、更新、删除、变更标题/描述/验收标准
- 默认表格输出，支持 `--json` 供脚本解析

> 当前实现主要基于禅道 RESTful API v1，默认请求路径形如
> `<zentao-url>/api.php/v1/...`。少量执行/需求关联能力使用禅道经典接口
> `<zentao-url>/index.php?...` 补齐。它不是官方 API 2.0 客户端；如果禅道部署在子路径下，
> 请填写禅道根地址，例如 `https://example.com/zentao`。

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

## WeCom long connection bot

The ADK agent team can be exposed through a WeCom intelligent bot long
connection. Configure the bot credentials in environment variables:

```env
WECOM_BOT_ID=your-bot-id
WECOM_BOT_SECRET=your-bot-secret
WECHAT_BOT_ID=your-bot-id
WECHAT_BOT_SECRET=your-bot-secret
WECHAT_BOT_WS_URL=wss://openws.work.weixin.qq.com
```

The bridge accepts either `WECHAT_BOT_ID` / `WECHAT_BOT_SECRET` or the older
`WECOM_BOT_ID` / `WECOM_BOT_SECRET` names. `WECHAT_BOT_WS_URL` is optional; the
SDK uses its default WebSocket URL when it is omitted.

Start the bridge:

```bash
zentao-wecom-bot
```

Run with Docker Compose:

```bash
docker compose up --build
```

Compose reads runtime configuration from the project `.env` file. The Docker
build ignores `.env`, so local credentials are not baked into the image. The
long connection bot only needs outbound network access, so no port mapping is
required.

Or run the module directly:

```bash
python -m zentao_agent.wecom_bot
```

The bridge uses `wecom-aibot-python-sdk`, listens for `message.text`, runs the
Zentao ADK app or root agent, and replies with SDK stream messages. Each WeCom
`chatid + userid` pair maps to a separate ADK session.

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
zentao project list
zentao execution list --project 12
zentao bug list --execution 303
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

建议先用 `product list` 找到产品 ID，再查询该产品下的需求：

```bash
zentao product list
zentao story list --product 5
```

## 项目命令

查看当前账号可见的项目列表：

```bash
zentao project list
zentao project list --json
```

只查看当前账号参与的项目：

```bash
zentao project list --mine
zentao project list --mine --json
```

查看项目详情：

```bash
zentao project view 12
zentao project view 12 --json
```

## 执行命令

执行列表必须指定项目 ID。建议先用 `project list` 找到项目 ID，再查询该项目下的执行：

```bash
zentao project list
zentao execution list --project 12
zentao execution list --project 12 --json
```

查看执行详情：

```bash
zentao execution view 303
zentao execution view 303 --json
```

关联已有需求到执行：

```bash
zentao execution link-story 303 --story 789
zentao execution link-story 303 --story 789 --json
```

## 任务命令

任务列表需要执行 ID。可以先用 `project list` 找到项目 ID，再用 `execution list --project ID` 找到执行 ID。

查看某个执行下分配给自己的任务：

```bash
zentao task list --execution 303 --mine
zentao task list --execution 303 --opened-by me
zentao task list --execution 303 --opened-by alice
```

`--opened-by` 会按禅道返回的 `openedBy` 字段在本地再次过滤；如果要完整统计跨页结果，请同时使用 `--all`。

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

创建任务：

```bash
zentao task create --execution 303 --name "实现批量导入" --est-started 2026-06-01 --deadline 2026-06-05 --type devel --assigned-to alice --estimate 2
zentao task create --execution 303 --name "编写测试用例" --est-started 2026-06-01 --deadline 2026-06-05 --type test --json
zentao task create --execution 303 --story 789 --name "实现需求 789" --est-started 2026-06-01 --deadline 2026-06-05
zentao task update 123 --name "更新后的任务标题" --desc "更新后的任务描述" --deadline 2026-06-10
zentao task delete 123 --yes
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

Bug 列表必须指定执行 ID。可以先用 `project list` 找到项目 ID，再用 `execution list --project ID` 找到执行 ID：

```bash
zentao project list
zentao execution list --project 12
zentao bug list --execution 303
```

查询分配给某个账号的 Bug：

```bash
zentao bug list --execution 303 --assigned-to alice
zentao bug list --execution 303 --opened-by me
zentao bug list --execution 303 --opened-by alice
```

`--opened-by` 会按禅道返回的 `openedBy` 字段在本地再次过滤；如果要完整统计跨页结果，请同时使用 `--all`。

按状态筛选：

```bash
zentao bug list --execution 303 --status active
```

查看 Bug 详情：

```bash
zentao bug view 456
zentao bug view 456 --json
```

创建 Bug：

```bash
zentao bug create --execution 303 --title "导入时报错" --steps "打开导入页面并提交文件"
zentao bug create --execution 303 --product 5 --title "导入时报错" --steps "打开导入页面并提交文件" --severity 2 --pri 2 --opened-build trunk --json
zentao bug update 456 --title "更新后的 Bug 标题" --steps "更新后的复现步骤" --severity 2 --pri 2
zentao bug delete 456 --yes
```

如果指定的执行 ID 不存在，或当前账号不可见，CLI 会返回禅道接口的错误信息。

## 需求命令

需求列表可以按产品 ID 查看产品需求池，也可以按执行 ID 查看该执行已关联的需求。`--product` 和 `--execution` 二选一：

```bash
zentao story list --product 5
zentao story list --execution 303
```

按状态筛选：

```bash
zentao story list --product 5 --status active
zentao story list --execution 303 --status active
zentao story list --product 5 --opened-by me
zentao story list --execution 303 --opened-by alice
```

`--opened-by` 会按禅道返回的 `openedBy` 字段在本地再次过滤；如果要完整统计跨页结果，请同时使用 `--all`。

查看需求详情：

```bash
zentao story view 789
zentao story view 789 --json
```

创建需求：

```bash
zentao story create --product 5 --title "支持批量导入客户" --spec "作为运营，我希望批量导入客户，以减少手工录入。" --verify "上传模板文件后，系统创建客户并返回导入结果。"
```

也可以直接在执行下创建需求。此时 `--product` 可省略，禅道会根据执行绑定的产品推断；如果执行绑定了多个产品，建议显式传 `--product`：

```bash
zentao story create --execution 303 --title "支持批量导入客户" --spec "需求描述" --verify "验收标准"
zentao story create --execution 303 --product 5 --title "支持批量导入客户" --spec "需求描述"
zentao story create --execution 303 --title "支持批量导入客户" --spec "需求描述" --status draft
```

常用可选参数：

```bash
zentao story create --product 5 --title "支持批量导入客户" --spec "需求描述" --verify "验收标准" --pri 2 --category feature --status draft --json
```

`story create` 默认创建草稿；如果要直接创建为激活状态，显式传 `--status active`。

变更需求标题、描述或验收标准：

```bash
zentao story change 789 --title "支持 Excel 批量导入客户" --spec "更新后的需求描述" --verify "更新后的验收标准"
zentao story change 789 --title "支持 Excel 批量导入客户" --spec "更新后的需求描述" --json
zentao story update 789 --title "支持 Excel 批量导入客户" --spec "更新后的需求描述" --verify "更新后的验收标准"
zentao story delete 789 --yes
```

`story create --product` 会先校验产品是否存在且当前账号可见，避免禅道接口在产品 ID 错误时回退到默认产品。使用 `--execution` 且不传 `--product` 时，由禅道根据执行绑定产品推断。

如果指定的产品 ID 不存在，或当前账号不可见，CLI 会报错而不是使用禅道接口的默认回退结果。

## JSON 输出

查询类命令支持 `--json`，适合自动化脚本。

```bash
zentao product list --json
zentao project list --json
zentao execution list --project 12 --json
zentao task list --execution 303 --mine --json
zentao task list --execution 303 --opened-by me --json
zentao task view 123 --json
zentao bug list --execution 303 --assigned-to alice --json
zentao bug list --execution 303 --opened-by me --json
zentao story list --product 5 --json
zentao story list --execution 303 --json
zentao story list --execution 303 --opened-by me --json
zentao story create --product 5 --title "支持批量导入客户" --spec "需求描述" --json
zentao story create --execution 303 --title "支持批量导入客户" --spec "需求描述" --json
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
zentao bug list --execution 303 --json | jq ".data[] | {id, title, status}"
```

## 分页

所有 `list` 命令默认只查询第 1 页，每页 100 条。可以用 `--page` 和 `--page-size` 控制分页：

```bash
zentao bug list --execution 303 --page 2 --page-size 50
zentao story list --execution 303 --page-size 200 --json
```

需要导出全量数据时，显式使用 `--all`。`--all` 会从指定页开始自动翻页，直到禅道接口返回全部记录：

```bash
zentao task list --execution 303 --all --json
zentao bug list --execution 303 --all --page-size 1000 --json
```

## 常见工作流

每天开始工作：

```bash
zentao product list
zentao project list
zentao execution list --project 12
zentao story list --execution 303
zentao task list --execution 303 --mine
zentao bug list --execution 303 --assigned-to alice --status active
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
zentao project list --json > projects.json
zentao execution list --project 12 --json > executions.json
zentao task list --execution 303 --mine --all --json > tasks.json
zentao bug list --execution 303 --all --json > bugs.json
zentao story list --execution 303 --all --json > execution-stories.json
zentao story list --product 5 --all --json > product-stories.json
```

产品经理创建并调整需求：

```bash
zentao product list
zentao story create --product 5 --title "支持批量导入客户" --spec "作为运营，我希望批量导入客户，以减少手工录入。" --verify "上传模板文件后，系统创建客户并返回导入结果。" --pri 2
zentao story change 789 --title "支持 Excel 批量导入客户" --spec "补充字段映射和错误行下载规则" --verify "导入后能看到成功数、失败数和失败明细"
zentao story view 789
```

## 手动 Smoke Test

连接真实禅道实例后，建议按顺序验证：

```bash
zentao product list
zentao product view 5 --json
zentao project list
zentao project view 12 --json
zentao execution list --project 12 --json
zentao execution view 303 --json
zentao bug list --execution 303 --json
zentao story list --execution 303 --json
zentao story list --product 5 --json
zentao task list --execution 303 --json
```

如果 `execution list --project 12`、`bug list --execution 303` 或 `task list --execution 303` 返回权限或上下文错误，请确认该项目/执行 ID 对当前账号可见。

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
    project.py
    execution.py
    task.py
    bug.py
    story.py
```

## 当前限制

- 当前实现按实际环境验证通过的 API v1 编写，不是官方 API 2.0 客户端。
- 少量能力使用经典 `index.php` 接口补齐，包括执行关联需求、执行下创建需求、根据执行推断产品。
- 产品和项目目前只支持只读查询。
- 执行支持查询和关联已有需求。
- 需求支持创建、更新和删除，暂不支持关闭、评审、拆分、指派或状态流转。
- Bug 列表必须传 `--execution`，需求列表必须传 `--product` 或 `--execution`。
- 任务列表必须传 `--execution`。
- 当前没有 `logout`、多 profile 和 keyring 存储。
- `task create/update/delete/comment/finish` 会直接修改禅道数据，请先在测试任务上验证。
- `bug create/update/delete` 会直接修改禅道数据，请先在测试 Bug 上验证。
- `execution link-story` 会直接修改禅道数据，请先在测试执行上验证。
- `story create/update/delete/change` 会直接修改禅道数据，请先在测试产品或测试执行上验证。
