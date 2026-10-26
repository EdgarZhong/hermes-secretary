# Validation证据索引

产品：3426c0fc9579dc0589fd0a831741b535aee71ca2。独立验收正式计划经主会话过目后执行，最终10项独立旅程通过／5.8秒，完整判据与17场景见上级validation.md。

全部原始证据在ignored `.hermes-dev/noting-chain-20261027/validation/`：

- `test_validation_journeys.py`、`run-final.log`：当前正式registry／typed工具／原生runner／Main／RPC的完整步骤与最终结果。
- `H01-H02-H04.json`、`H03.json`、`H04-bound.json`、`H05-H06.json`：三模式范围、四字段、闭端点、200/201、跨域／Noting父域／fork/rewind、工具配对分页及native压缩。
- `N01-N02-N03-N06-R01.json`、`N04-N05.json`：跨Turn同Task、后Task追加、no-op、Evidence time、Candidate二选一与已提交节点保护、Main权限和建议输出。
- `R02.json`、`R03.json`：正式RPC恢复同Task槽位／幂等、有效pointer及busy队列发布。
- `M01-M02.json`、`model-actions-and-reuse.json`：独立重新解析原始两Task六wire及Notebook，列8个采样后源码差异，明确真实模型证据适用范围。
- `plan-before-execution.md`：获主会话过目的完整计划；`run-1.log`至`run-5.log`和`journeys-run*-source.py`：保留夹具错误及定向修正／复验历史。无产品修复。

复用机制原件为同ignored父目录的 `final-integration-tests.log`（1094项）、`review-evidence/history-v01-tests-final.log`（107项）、`release/linux-final-tests.log`（132项）与Linux Git blob核验。真实模型原件在 `e2e/live/`，不把早期样本冒称当前全部源码同SHA模型测试。没有重跑大型套件或任何新外部模型调用，没有访问生产或用户页面。
