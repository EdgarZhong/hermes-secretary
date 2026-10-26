# 本轮实施计划：20261027-noting-provenance-history

## 目标与依据

按snapshot-index与baseline冻结实现C01–C20，主优先级为History正式入口与Notebook提交形成完整纵向链；已审Prompt同步。开发环境复用原官方PM `.venv`，lock／依赖不变；测试只用`HERMES_PYTHON="$PWD/.venv/bin/python" scripts/run_tests.sh`。本轮分支隔离main与原目录dirty；保留common post-commit自动push hook。

## 覆盖与任务

| 要求/口径编号 | 任务和正式路径 | 实现负责人及白名单 | 依赖和接口 | 验证方法 | 用户场景 | 完成条件 |
|---|---|---|---|---|---|---|
| C09–17、20 | H：conversation_history→合法路径／候选流→分类过滤／Get Meta／工具配对投影 | History Agent；tools/session_history_tool.py、tools/conversation_history_*.py新sibling、hermes_state_conversation_history.py、hermes_state_message_provenance.py及专属History测试 | include_auxiliary顶层；mode=get_meta；include原Search语义；不改Notebook模块及agent/system_prompt | 正式SessionDB＋Main／Noting工具调用、cross／fork／rewind、辅助载体／闭端点／超容量／工具配对／清理失败反例 | S1–S4 | 参数声明、真实handler、所有模式无旁路且结果与要求一致 |
| C04–08、20 | N：Notebook工具→WorkingState→不可变item／Snapshot→所有模型及正式读视图 | Notebook Agent；secretary/notebook_*.py、secretary/noting_contract.py、hermes_state_secretary_notebook.py及必要Notebook状态层、新专属测试与harness | 编辑源输入保留source_message_uids一维表示本Task槽；对外provenance二维UID链，内部身份沿既有归属；Evidence time一维时刻／区间链；Candidate refs二选一 | 同Task多次／跨Turn、次Task追加、拒绝原子性、no-op、restart／fork／rewind、readonly时间及所有投影、Snapshot正式commit | S5–S8 | 正式持久链＋读视图＋源权限全闭合，不建兼容层 |
| C02–03、18–20 | P：Noting Task及Main History guidance与必要Prompt接线 | Prompt Agent；secretary/noting_prompts.py、agent/system_prompt.py、新tests/secretary/test_noting_history_tuning_prompt.py | 等待接口采用已定名get_meta/include_auxiliary/source_message_uids；不改schema，Prompt不复制Schema／内部审计对象 | 真实构建全Prompt／权限／无改动样本；复用结构证据，主会话统一真实模型取证 | S9 | 已审英文精简替换，清退／续Turn结束语句保持 |
| C01、20 | I：主会话亲审、集成、模型链路、一次性数据方案、发布与只读终验 | 主会话；核心文档、轮次文档、必要接线微修、ignored运行脚本；不碰原dirty／前端 | H/N/P整包交回；两个独立门禁通过；上线沿既有SOP工具 | 原生合成隔离Profile完整任务及真实模型，正式机Linux定向／版本／数据指纹，回滚点与备份轮换 | S10 | 测好、提交push、上线、目标转换及服务／数据结果可信 |

## 当前状态与编排

| 目标/任务 | 机制实现 | 正式接线 | 针对性验证 | 用户结果 | 当前负责人和下一步 |
|---|---|---|---|---|---|
| H | 完成；C14／V01已关闭 | 正式handler／同UID辅助投影 | 当前107项及Linux132项等覆盖，十检查通过 | 双独立门禁通过，已上线 | 无剩余 |
| N | 完成 | 可信Task／恢复／Candidate切换已接 | 来源／时间／原子失败及正式恢复通过；旧失败单列 | 双门禁／实际型号样本及生产目标转换通过 | 无剩余 |
| P | 完成且亲审 | 完整Main／Noting／续Turn构建 | 已审文案、权限／请求冻结、k3.1-pro两Task6请求通过 | 双独立门禁通过，已上线 | 无剩余 |
| I | 完成 | origin/main→生产main及唯一转换正式接线 | Linux132、双门禁、RPC／数据／保护指纹／两套备份终验通过 | 已上线3426c0f，receipt=verified | 交付记录已落实，无新阻塞 |

同一工作区独立文件白名单并行；测试harness共享改动归N，H不得改Notebook测试，P只新建自有测试。子Agent不派生、不提交；整包完成集中交回，只有真阻塞／权限／跨包接口决策才中途消息，禁止流水账。每次UI任务重申隐藏IAB限制。

## 缺陷与整改

| 问题编号 | 要求与触发条件 | 当前事实与影响 | 优先级及理由 | 修复负责人 | 关闭与复验条件 | 状态 |
|---|---|---|---|---|---|---|
| I01 | C03，用户仅说稍后处理 | 首真实模型样本补建议并重写description，违反正文保持 | 高／核心用户边界 | P＋主会话 | 明确直接分流及字段名，实际k3.1-pro两Task通过；旧别名失败保留 | 已通过实际型号场景 |
| I02 | C07/C13，辅助载体与真人相似正文 | Evidence time旧分类及新History body fallback分别可抢优先级／误降真人 | 高／同一真实来源必须一致 | H/N | 统一可信enrichment；真实metadata/receipt与真人5反例、所有模式无写，99项结合及171项History通过 | 已关闭 |
| I04 | C14，显式辅助读压缩消息 | full=False前置丢弃summary；mixed同UID系统部分不可达 | 高／已要求模式可达 | H | 窄辅助投影、mixed角色选择、原权限／原文保护201项通过 | 已关闭 |
| I05 | C06，同Task Candidate direct→refs | 当前工作槽与新链不可删规则需区分 | 中／保留原合法操作 | N | 仅未提交当前唯一槽可换，旧Task节点拒绝，正式恢复及原子性98项通过；已提交同owner也拒绝 | 已关闭 |
| I03 | C11，真人Steer运行时长框架 | 外壳占满Get Meta预览 | 中／识别能力 | 主会话 | 可信steer标准外壳最小清理，38项通过；原文不变 | 已定向通过 |

## 取舍、快照与续接

初始产品基线main d1de4db49b，旧目录219bfc22ea。基线文档包含当前根README／AGENTS／CLAUDE及最新07／索引，保留旧R20实现事实。已存在common hook与仓库模板内容一致。`.venv`指向原官方PM已建环境，不安装依赖或改lock。真实模型只在隔离Profile、虚构内容、cwd仓库外进行；生产读写按C01及SOP，不能写测试记录／重放业务消息。必要调用有预算、保失败与实际usage，不外发测试微信／飞书。上线自然空闲窗口，不能打断生产Turn。

主会话最终集成：40文件定向回归1094项已通过，10项冻结检查已通过；开发期各包机制／原生接线／真实模型证据已齐，产品快照提交后独立Verification及Linux针对同一版本审查。该段为进入门禁时点；最终发布及判定见下方最终交付状态。

独立初审4032f44：38项覆盖，唯一V01导致C11/C20/R12不通过（误删真人Gateway纯文本粘贴）；主会话提案撤回该额外清理已获评审接受，实现端原反证及107项定向通过、十检查通过。修复快照提交后安排全新第三方全范围复审，未提前放行Validation／生产。

最终产品3426c0fc9579dc0589fd0a831741b535aee71ca2：全新Verification重新建38判据后37符合／1生产执行本地不适用，原V01未改断言反证通过，无新增整改。主会话已接收。最终Linux7文件132通过、18,394 tracked Git blobs按原attributes核对；最终代码再次验证目标转换副本51版本／8Snapshot／累计55节点／180 UID／162投影，integrity及FK通过。独立Validation先制定场景待主会话过目。发布仍未实施；先将通过双门禁版本快进远端main，再stage／自然空闲停服／三库备份／目标一次转换／启动核验。原本地main工作区他人dirty不触碰。

## 最终交付状态

2026-10-27：H/N/P/I全部完成。全新Verification38项37符合／1本地生产不适用，Validation17适用场景及10独立正式旅程通过，无新增整改。主会话亲审两报告和核心原始输出后，将3426c0f快进合入origin/main，生产保持main从6ef9459快进发布。预检脚本一次因重复UID误选最后一物理行而拒绝，已沿正式转换器setdefault语义取首个合法来源、重验51／8／81通过；失败未写生产，也未改manifest绕过。

实际发布receipt=verified；唯一目标51版本／8Snapshot／pointer、31独立Task节点累计55次／180UID引用、162投影全部通过，非目标数据及schema、配置／绑定／静态保持。Web/Gateway3426c0f active／running、微信connected；正式REST／RPC／HTTP静态及生产只读转换复验通过。两套三库逐SHA／integrity／FK通过，研究副本两文件313,501,635字节清退；没有生产模型或测试外发。运维事实以operations-log顶部为准，最终判定见final-delivery.md。

I01–I05及原审I-V01全部关闭；无本轮范围内未完成／阻塞。29＋Prelude15冻结基线失败保持范围外，未放宽规则。两项工程细化仍明确待用户追认，不冒称用户已确认。后继文档commit不改变实际部署3426c0f。
