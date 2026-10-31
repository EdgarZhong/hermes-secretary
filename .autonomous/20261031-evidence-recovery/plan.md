# 20261031-evidence-recovery · 实施计划

## 1. 目标与依据

依据snapshot-index.md及baseline.txt。仅实施证据组描述与Main强制历史核对，沿已有Notebook不可变版本、Snapshot、History／Prompt构建、工具权限。PM环境复用主仓官方.venv且lock一致；生产Alex空闲发布，配置／数据／静态保护、三库备份最近两套。

## 2. 覆盖与任务

| 要求 | 任务／owner及白名单 | 正式路径与依赖 | 验证与用户场景 | 完成条件 |
|---|---|---|---|---|
| E01/02/04/06 | D1 数据与工具：实现Agent；secretary/notebook_{contract,model,items,render,store}.py、secretary/noting_tools.py、对应tools Schema／state持久化必要接缝及tests中对应文件 | create/update→working→immutable version→Snapshot→Main/Noting/Framework/回执；保持旧组不变 | 真DB跨Task同槽覆盖／追加、旧节点拒绝改、UID／description同步、时间不读description、Candidate refs/direct、旧组可读、拒绝无副作用 | 新组描述正式链路可用且边界回归通过 |
| E01/02/05/07 | D2 Prompt：实现Agent；agent/system_prompt.py、secretary/noting_prompts.py及专属tests | 实际root构造／restore／Noting task/control/continuation；依赖D1字段接口供集成 | visible原文无需读／indexed先Read／missing再Search／失败未知；非Main／开关权限／cache-prefix | 定稿逐字落运行常量，无竞争旧指引 |
| E01–09 | I1 集成／主会话；根三文档、07、.autonomous本轮、ignored证据／模型脚本 | review两包、正式构造全Prompt、受控SDK正式入口及父子工具／前缀验证（用户取消后续真实模型） | 多样Main回查分支＋Noting描述仅本组／跨Task；真实工具执行和受控响应最终输出 | 必要机制及冻结十检查通过；不声称模型服从率 |
| E01–09 | V1 独立Verification（只读产品，写verification.md） | 集成收敛后新无上下文Agent，先规格判据再实现；复用有效测试 | 全范围逐条矩阵与反证 | 无范围内违规／证据不足 |
| E01–09 | V2 独立Validation（只读产品，写validation.md及ignored运行证据） | V1通过后新无上下文Agent，计划先交回、原生入口隔离受控SDK操作；用户取消真实模型验证 | 典型历史恢复／可见直接用／缺索引搜索／失败未知／Noting创建修改链 | 全适用场景通过 |
| E03/08/09 | R1 发布／主会话；operations-log、CLAUDE、README必要稳定事实、本轮final-delivery | 两门禁→提交push→main快进→Alex空闲预检复检／备份／正式既有执行器→缓存正常边界失效 | 真Linux目标测试、两服务实际版本、健康／微信connected、Notebook／Schedule数据保护、缓存清理回执 | receipt verified及上线核验，备份收尾，交付 |

## 3. 当前状态与编排

D1/D2并行，文件边界不交叉；主会话统一review、集成及提交。不得改对方文件，不另派子Agent，不部署、不写生产、不自行commit。实现整包交回；普通步骤／命令／小发现写证据，不发送流水账。两个独立门禁顺序执行，复用同版本有效证据；修复定向补证。

| 目标 | 机制 | 正式接线 | 定向验证 | 用户实际结果 |
|---|---|---|---|---|
| 证据组描述 | D1已交回并亲审 | 全链已接 | 151＋62及权限86等通过，独立产品门禁已通过 | 按E12采用受控SDK，独立Validation通过 |
| Main核对 | D2已交回并亲审 | 全Prompt与恢复已接 | 33项通过，真实模型后续已取消 | 独立Validation通过 |
| 上线 | — | 正式发布完成 | 产品两门禁及Linux111通过 | bf28ab5 verified，读验／保护／两套备份通过；所有附加工作树已清理 |

## 4. 缺陷与整改、取舍与快照

新增D3：移植已获授权manual Noting debug遗留包，仅七个代码／契约／测试文件及当前生命周期必要适配，报告manual-debug.md，不启动生产Noting。用户E12取消新真实模型验证，保留此前3样本／6HTTP200，不以缺采样阻断。

新增W1：主会话按用户E10授权审计所有本仓worktree、整合未覆盖且已确认范围内改动，保留必要ignored证据后清理旧工作树，释放main占用，原目录检出最新main。独立审计Agent只读写worktree-audit.md，不能删除／切换／提交。

暂无范围内缺陷。旧来源补描述未获授权，不自动迁移；保持missing而非猜造。字段名称和兼容投影由既有API增量契约收敛后主会话review记录；不得降低旧节点不可变、来源准入或Snapshot提交校验。

冻结提交见baseline.txt。基线产品c07b038d1c，正式已运行ef9051f。原聊天目录dirty已保全并按当前事实整合，清理后检出main。完成证据按实际版本记录，不能以服务active替代模型行为验收。

产品集成a51a0bf已由两个独立门禁关闭。Linux111/0、十检查通过。只读生产兼容：三Profile0写，Alex132个现行UID链历史item的204组缺描述投影null；58个更早非链历史item仅保持原样，不宣称已转换。正式发布及清理事实由原独立门禁补核。

实际发布bf28ab5 verified，postrelease读验及两套三库轮换已完成。全部六附加实体工作树和失效登记已清，13本地功能分支经安全确认后删除；只剩原根main工作树，原环境／stash及其它仓库保持。两门禁补核最终收据，不重跑产品测试；最终判定见final-delivery.md。
