"""Non-executing rejection for historical Memo calls; never registered."""

import json


def noting_memo(*args, **kwargs):
    from tools.secretary_dispatch import legacy_tool_removed
    return json.dumps(legacy_tool_removed("noting_memo"), ensure_ascii=False)
