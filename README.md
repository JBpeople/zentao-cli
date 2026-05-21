# zentao-cli

面向禅道开源版 21.7.5 的 Python 命令行客户端。

首版目标是覆盖个人日常任务处理和脚本自动化：

- 交互式登录：`zentao login`
- 当前账号查看：`zentao whoami`
- 任务处理：查询、查看、更新状态、评论、完成
- Bug 只读：查询、查看
- 需求只读：查询、查看
- 默认表格输出，支持 `--json` 供脚本解析

> 当前实现基于禅道 RESTful API v1，默认请求路径形如
> `<zentao-url>/api.php/v1/...`。如果你的禅道部署在子路径下，登录时请填写禅道根地址，例如
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

也可以不依赖 console script，直接运行模块：

```bash
python -m zentao_cli.main --help
```

## 登录

运行：

```bash
zentao login
```

按提示输入：

```text
Zentao URL: https://zentao.example.com
Username: alice
Password:
```

登录成功后，CLI 会保存会话信息，不保存明文密码。

查看当前登录账号：

```bash
zentao whoami
```

本地配置由 `platformdirs` 决定保存位置。Windows 上通常在：

```text
C:\Users\<you>\AppData\Local\zentao-cli\config.toml
```

配置内容类似：

```toml
[default]
base_url = "https://zentao.example.com"
username = "alice"
session_name = "zentaosid"
session_id = "..."
```

## 任务命令

查看分配给自己的任务：

```bash
zentao task list --mine
```

按状态筛选：

```bash
zentao task list --mine --status doing
zentao task list --status wait
zentao task list --status done
```

按项目 ID 筛选：

```bash
zentao task list --project 12
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

查询 Bug。未指定产品时，CLI 会先读取你有权限访问的产品列表，再逐个查询产品下的 Bug：

```bash
zentao bug list
```

只查询某个产品：

```bash
zentao bug list --product 5
```

如果指定的产品 ID 不存在，或当前账号不可见，CLI 会报错而不是使用禅道接口的默认回退结果。

查询分配给某个账号的 Bug：

```bash
zentao bug list --assigned-to alice
```

如果你的禅道 API 支持 `me` 作为当前用户，也可以尝试：

```bash
zentao bug list --assigned-to me
```

按状态筛选：

```bash
zentao bug list --status active
```

查看 Bug 详情：

```bash
zentao bug view 456
```

## 需求命令

查询需求。未指定产品时，CLI 会先读取你有权限访问的产品列表，再逐个查询产品下的需求：

```bash
zentao story list
```

按产品 ID 筛选：

```bash
zentao story list --product 3
```

如果指定的产品 ID 不存在，或当前账号不可见，CLI 会报错而不是使用禅道接口的默认回退结果。

按状态筛选：

```bash
zentao story list --status active
```

查看需求详情：

```bash
zentao story view 789
```

## JSON 输出

所有查询类命令支持 `--json`，适合自动化脚本。

示例：

```bash
zentao task list --mine --json
zentao task view 123 --json
zentao bug list --assigned-to alice --json
zentao story list --product 3 --json
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

PowerShell 中可以这样保存结果：

```powershell
zentao task list --mine --json > tasks.json
```

配合 `jq` 时：

```bash
zentao task list --mine --json | jq ".data[] | {id, name, status}"
```

## 常见工作流

每天开始工作：

```bash
zentao task list --mine
zentao bug list --assigned-to alice --status active
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

生成脚本输入：

```bash
zentao task list --mine --json > my-tasks.json
```

## 手动 Smoke Test

连接真实禅道开源版 21.7.5 后，建议按顺序验证：

```bash
zentao login
zentao whoami
zentao bug list --json
zentao bug list --product 5 --json
zentao story list --product 5 --json
zentao task list --mine
zentao task list --mine --json
```

如果 `task list --mine` 返回权限或上下文错误，说明该禅道实例要求任务按项目或执行上下文查询，需要再针对当前部署补任务接口适配。

如果列表命令可用，再验证写操作：

```bash
zentao task update 123 --status doing
zentao task comment 123 "CLI smoke test"
```

确认无误后，再尝试：

```bash
zentao task finish 123 --comment "CLI smoke test done"
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
src/zentao_cli/
  main.py              # Typer 入口
  config.py            # 本地配置读写
  auth.py              # 登录和 profile 加载
  client.py            # Zentao API v1 HTTP client
  models.py            # Task/Bug/Story 等归一化模型
  formatters.py        # JSON 输出和表格辅助
  errors.py            # 用户可见异常
  commands/
    task.py
    bug.py
    story.py
```

## 当前限制

- 只面向禅道开源版 21.7.5 的 API v1。
- Bug 和需求目前只支持只读查询。
- 当前没有 `logout`、多 profile、环境变量覆盖和 keyring 存储。
- Bug 和需求列表基于产品上下文查询；不传 `--product` 时会聚合所有可见产品的第一页结果。
- 任务列表接口在不同禅道部署中可能需要项目或执行上下文，若 `/tasks` 不可用，需要在 `src/zentao_cli/client.py` 中继续适配。
- `task update/comment/finish` 会直接修改禅道数据，请先在测试任务上验证。
