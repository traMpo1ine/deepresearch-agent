# SQLite Migration 学习笔记

## 为什么做

Agent memory 是长期运行产物。后续新增 verification trace 字段、repair 统计字段时，旧数据库不应该因为缺列直接崩掉。

## 怎么实现

- `SQLiteMemoryStore._ensure_column()` 用 `PRAGMA table_info` 检查列是否存在。
- 当前对 `verification_traces.atomic_results` 做了安全补列。
- `schema_migrations` 表记录已应用版本和说明。
- `PRAGMA user_version` 记录当前 SQLite schema version。
- `SQLiteMemoryStore.schema_version()` 返回当前版本。
- `SQLiteMemoryStore.list_schema_migrations()` 返回已应用 migration 列表。

当前版本：

- v1：Initial persistent memory schema with verification traces。
- v2：Add atomic verification results to verification_traces。

## 旧库升级样例

测试里手工构造一个旧版 `verification_traces` 表，故意缺少 `atomic_results`：

```python
with sqlite3.connect(path) as conn:
    conn.execute("CREATE TABLE verification_traces (...)")
    conn.execute("PRAGMA user_version = 1")

store = SQLiteMemoryStore(path)
```

重新初始化 store 后：

- `atomic_results` 会被自动补列。
- `schema_version()` 变成 2。
- `schema_migrations` 里有 v1 和 v2 记录。

## 失败案例和权衡

SQLite migration 不应该过度设计。当前项目还处在离线学习阶段，先采用可读的补列策略。等 schema 变化明显增多，再考虑版本化 migration 函数列表。
