# 毕业生就业信息管理系统（演示版）

## 运行

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
flask --app app init-demo
python app.py
```

浏览器打开 <http://127.0.0.1:5000>。

## 局域网访问

启动后，在运行电脑上执行 `ipconfig`，找到当前 Wi-Fi 或以太网网卡的 IPv4 地址，例如 `192.168.1.20`。

同一局域网的其他设备访问：

```text
http://192.168.1.20:5000
```

如果 Windows 防火墙弹出提示，请允许 Python 通过专用网络访问。也可以使用管理员 PowerShell 添加端口规则：

```powershell
New-NetFirewallRule -DisplayName "Flask Employment Demo 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Private
```

仅在可信的家庭或校园局域网中使用此演示配置，不要直接暴露到公网。

## 演示账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 学生 | `student001` | `123456` |
| 就业办工作人员 | `admin` | `admin123` |

## 功能

- 学生查看个人档案，录入或修改就业时间、单位、单位性质、岗位、档案发往地和备注。
- 每次保存自动进入“待审核”状态。
- 工作人员按姓名/学号/状态查询，审核通过或驳回并填写意见。
- 工作人员查看总体审核数量和按单位性质统计。

这是用于课程演示的简化版本，默认使用项目目录下的 SQLite 文件 `employment.db`。
