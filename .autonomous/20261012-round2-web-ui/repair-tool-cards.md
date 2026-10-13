# 同一工具调用卡片整改

2026-10-13，Main 集中审查记录；仍待当前终态修复后的实际复核，不构成独立验收。

- 依据：06 工具卡 Parameters / Result 合卡及用户 C44、C47；按真实 call UID / call_id 与 scope 关联，不按工具名猜测。
- 实现：前端 `projection.ts` 的 `combineToolCards` 消费原生调用 sidecar 与 result owner；精确UID优先，冲突不回退，复用ID歧义保Unknown；正式 `App.tsx` 在Timeline接此投影并移除旧独立历史参数卡。
- Main review：读取完整关联实现、scope/session保护、JSON UID映射与重复occurrence、历史owner替换live副本接线；既有63例关联合同与附件15例合78例证据按原owner报告复用，不重跑。
- 正式IAB：会话 `20261013_111430_4c8d85` 中 terminal、search_files、read_file、noting_memo 均为一张按钮卡包含Parameters与Result；原文件User只显示原输入与文件名，未把原生注入全文当消息正文。DOM证据见 ignored `main-final-integration/repair-history-before-native.dom.txt`。
- 新反例：被用户Stop的vision_analyze真实结果为 `[Tool execution cancelled — vision_analyze was abandoned: explicit stop requested]`，当前解析把非JSON包装误标Success；已交当前projection owner按原生明确终止包装修复，不匹配普通正文单词，不隐藏结果。
- 最终新Turn工具进行中、完成、失败／中断现场证据待Main补；不凭helper测试写闭合，不改变执行事实或原生消息。

## Main 最终集成接收

2026-10-13：Main集中亲审正式路径与改动并接收相应owner证据，最终前端c55120f、visual fc18614、原生产品4443aa7。用户自测整改的实际关闭范围、测试失败/修复留痕、真实DeepSeek/IAB及未验证边界统一见final-delivery「当前整改关闭证据」和根CLAUDE；本报告上方“待实测”是交回时观察，不覆盖该最新接收。最终冻结前端health0/0及build/types通过；两独立门禁未执行，不称整轮验收。
