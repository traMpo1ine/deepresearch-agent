# Week 02: DAG and State Machine

本周目标是把研究任务从线性流程升级为可并发、可阻塞、可恢复的 DAG。

核心学习点：

- DAG 用依赖边表达任务关系。
- 拓扑批次允许同层任务并发执行。
- 状态机让任务生命周期显式化：PENDING、READY、RUNNING、SUCCEEDED、FAILED、BLOCKED、REPAIRING、VERIFIED。
- 下游依赖失败节点时进入 BLOCKED，而不是静默跳过。

当前代码入口：

- `src/deepresearch_agent/orchestration/dag.py`
- `src/deepresearch_agent/orchestration/state_machine.py`
