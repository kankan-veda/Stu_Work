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
