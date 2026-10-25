"""Cross-process formal writer wakeups reuse the existing sessions.changed watcher."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from hermes_state import SessionDB
from hermes_state_history_notifications import notification_path
from tui_gateway import server


@pytest.mark.parametrize("operation",["replace","edit"])
def test_external_same_count_writer_wakes_only_its_real_profile(tmp_path,monkeypatch,operation):
    home=tmp_path/"main"
    other=tmp_path/"other"
    home.mkdir();other.mkdir()
    monkeypatch.setenv("HERMES_HOME",str(home))
    with SessionDB(db_path=home/"state.db") as db, SessionDB(db_path=other/"state.db") as foreign:
        for owner in (db,foreign):
            owner.create_session("same",source="desktop")
            owner.append_message("same","user","before")
        monkeypatch.setattr(server,"_watcher_home",lambda:home)
        monkeypatch.setattr(server,"_served_profile_homes",[other])
        before=server._sessions_sig()
        script='''import sys
from pathlib import Path
from hermes_state import SessionDB
with SessionDB(db_path=Path(sys.argv[1])) as db:
    if sys.argv[2]=='replace': db.replace_messages('same',[{'role':'user','content':'after'}])
    else: db.set_user_message_content('same',db.get_messages('same')[0]['id'],'after')
'''
        subprocess.run([sys.executable,"-c",script,str(other/"state.db"),operation],check=True,timeout=15)
        after=server._sessions_sig()
        assert after[0] == before[0] and after[1] != before[1]
        assert not notification_path(home/"state.db").exists()
        assert notification_path(other/"state.db").exists()
        assert foreign.get_session("same")["message_count"] == 1
        events=[]
        monkeypatch.setattr(server,"_broadcast_global_event",lambda kind,payload:events.append((kind,payload)))
        monkeypatch.setattr(server,"_change_sigs",{"sessions.changed":before})
        monkeypatch.setattr(server,"_change_checked_at",{})
        monkeypatch.setattr(server,"_change_broadcast_at",{})
        monkeypatch.setattr(server,"_CHANGE_WATCHES",{"sessions.changed":(0.5,server._sessions_sig,lambda:{})})
        server._broadcast_watched_changes(now=100)
        assert events == [("sessions.changed",{})]


def test_no_change_and_notification_failure_do_not_change_writer_contract(tmp_path,monkeypatch):
    with SessionDB(db_path=tmp_path/"state.db") as db:
        db.create_session("same",source="desktop")
        row_id=db.append_message("same","user","before")
        assert db.set_user_message_content("same",row_id,"before") == 1
        assert not notification_path(db.db_path).exists()
        db.replace_messages("same",db.get_messages("same"),archive_dropped=True)
        assert not notification_path(db.db_path).exists()
        monkeypatch.setattr("hermes_state_history_notifications.notification_path",lambda _path:tmp_path)
        assert db.set_user_message_content("same",row_id,"after") == 1
        assert db.get_messages("same")[0]["content"] == "after"
        assert db.replace_messages("same",[{"role":"user","content":"replacement"}]) is None
        assert db.get_messages("same")[0]["content"] == "replacement"


def test_rewind_signature_moves_even_when_counts_restored(tmp_path,monkeypatch):
    with SessionDB(db_path=tmp_path/"state.db") as db:
        db.create_session("same",source="desktop")
        db.append_messages_batch("same",[{"role":"user","content":"ask"},{"role":"assistant","content":"answer"}])
        monkeypatch.setattr(server,"_watcher_home",lambda:tmp_path)
        monkeypatch.setattr(server,"_served_profile_homes",[])
        before=server._sessions_sig()
        db.rewind_to_message("same",db.get_messages("same")[0]["id"])
        db.append_message("same","assistant","replacement")
        assert server._sessions_sig() != before
