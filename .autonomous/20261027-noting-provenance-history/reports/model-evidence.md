# 主会话真实模型取证

仅隔离Profile／虚构对话，经正式`_make_agent → 原生AIAgent → run_noting_task → 六工具handler → SQLite Snapshot`；生产配置、消息、渠道未改，不发微信／飞书。cwd在仓库Git root外，原Alex配置／SOUL／env／auth逐SHA保持。凭据仅原生环境引用，值不入Git或输出。

线上只读核对Alex config及置顶Session.model均为`k3.1-pro`、原生`kimi-coding`／`https://api.kimi.com/coding/v1`、high。最终harness使用相同型号／路由，两个独立Task均正常finish提交，共6次实际HTTP请求全部200。顶层工具及root在全部6个实际wire中分别只有一个SHA；child构造与父冻结root／tools完全一致。`conversation_history`实际选择Get Meta取得精确UID，未调用非白名单工具。不是mock模型结果。

第一Task把12盒改为18盒并保留S-17／可退货／未下单；税表“稍后处理”只增加Schedule建议及本Task新来源节点，正文／done／其它属性保持；已有真实排期的取书条目完全保持。第二Task只有Assistant提示未获用户回应，完整Notebook条目不变，无新item或来源节点。旧来源节点／Evidence time保持，新节点时间按原消息派生。机制同Task多调用／续Turn／恢复／下一Task追加及失败原子性由对应正式DB／runner集成测试补齐，不靠随机模型制造竞态。

最终实际usage：Task1 in=15182/out=1306/cache_read=72192/reasoning=634/4calls；Task2 in=6266/out=1192/cache_read=36608/reasoning=937/2calls。原生estimated_cost_usd为0但缺实际账单，不据此声称免费。

失败及修订原样保留：最初两次误沿旧harness别名`kimi-for-coding`，均顺手改税表description；不能等同当前线上型号。Task第2步忠于既定语义改成直接“稍后处理”条件，明确只改schedule_suggestion与source_message_uids，另澄清本Task一维数组。首次实际k3.1-pro税表已正确，但harness没提供取书已排期证据，模型合法补建议触发过严的无关记录断言；已用正式SchedulerStore实际登记并在可见回复提供登记证据，保持原断言后最终两Task通过。未把失败样本删除、松断言或改成mock。

私有证据：`.hermes-dev/noting-chain-20261027/e2e/live/`的result／6份wire／两份child transcript、request-audit、usage、outcome／前后Notebook和真实已有排期；失败目录`failed-schedule-description`、`failed-schedule-description-clarified`、`book-gap-fixture`。原harness及日志同父目录，0700／0600。最终脚本每轮最多16请求，只允许该原生Kimi推理endpoint；原Profile SHA保持。样本受测源文件SHA在result.product_sha256，后继仅Candidate来源形式切换和Compression辅助读取修复不涉及本样本输入／执行分支，须以正式受控DB及接口构建补证，不能把本模型样本冒称覆盖新增分支。
