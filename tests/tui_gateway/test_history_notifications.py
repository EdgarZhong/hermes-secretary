"""Cross-process formal writer wakeups reuse the existing sessions.changed watcher."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from hermes_state import SessionDB
from hermes_state_history_notifications import notification_path, secretary_notification_path
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


def test_gateway_turn_release_wakes_connected_watcher_after_final_history_was_seen(tmp_path, monkeypatch):
    """The last message can be observed while Gateway still holds the Turn lease."""
    home, other = tmp_path / 'alex', tmp_path / 'other'
    home.mkdir(); other.mkdir()
    with SessionDB(home / 'state.db') as db, SessionDB(other / 'state.db') as foreign:
        for owner in (db, foreign):
            owner.create_session('same', source='desktop')
            owner.append_message('same', 'user', 'Question')
        monkeypatch.setattr(server, '_watcher_home', lambda: other)
        monkeypatch.setattr(server, '_served_profile_homes', [home])
        script = '''import os, sys
from pathlib import Path
from types import SimpleNamespace
from hermes_state import SessionDB
from agent.turn_facade_lease import DurableTurnLease
with SessionDB(Path(sys.argv[1])) as db:
    holder = f'pid={os.getpid()}:turn=gateway-turn:platform=weixin'
    assert db.try_acquire_session_turn_lease('same', holder)
    db.append_message('same', 'assistant', 'Gateway final answer', turn_lease_holder=holder)
    print('persisted', flush=True)
    assert sys.stdin.readline().strip() == 'release'
    DurableTurnLease(SimpleNamespace(_active_session_turn_lease_holder=holder), db, 'same', holder).release()
'''
        child = subprocess.Popen([sys.executable, '-u', '-c', script, str(home / 'state.db')],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            line = child.stdout.readline().strip()
            if line != 'persisted':
                _, error = child.communicate(timeout=5)
                raise AssertionError(error)
            assert db.get_messages('same')[-1]['content'] == 'Gateway final answer'
            # Simulate the preceding notification already consumed BEFORE release.
            before = server._sessions_sig()
            child.stdin.write('release\n'); child.stdin.flush()
            _, error = child.communicate(timeout=15)
            assert child.returncode == 0, error
            after = server._sessions_sig()
            assert after[0] == before[0] and after[1] != before[1]
            assert after[1][1] == before[1][1]  # no new session/message row needed
            assert notification_path(home / 'state.db').exists()
            assert not notification_path(other / 'state.db').exists()
            assert db._read_one('SELECT holder FROM session_turn_leases') is None
            events = []
            monkeypatch.setattr(server, '_broadcast_global_event', lambda kind, payload: events.append((kind, payload)))
            monkeypatch.setattr(server, '_change_sigs', {'sessions.changed': before})
            monkeypatch.setattr(server, '_change_checked_at', {})
            monkeypatch.setattr(server, '_change_broadcast_at', {'sessions.changed': 99.0})
            monkeypatch.setattr(server, '_CHANGE_WATCHES', {'sessions.changed': (0.5, server._sessions_sig, lambda: {})})
            server._broadcast_watched_changes(now=100.0)
            assert events == []  # burst floor retains its trailing edge
            server._broadcast_watched_changes(now=101.1)
            assert events == [('sessions.changed', {})]
        finally:
            if child.poll() is None:
                child.kill(); child.communicate(timeout=5)


def test_turn_release_noop_and_signal_failure_preserve_native_lease_contract(tmp_path, monkeypatch):
    with SessionDB(tmp_path / 'state.db') as db:
        db.create_session('stored', source='desktop')
        assert db.try_acquire_session_turn_lease('stored', 'owner')
        marker = notification_path(db.db_path)
        db.release_session_turn_lease('stored', 'wrong-owner')
        assert not marker.exists()
        monkeypatch.setattr('hermes_state_history_notifications.notification_path', lambda _path: tmp_path)
        assert db.release_session_turn_lease('stored', 'owner') is None
        assert db._read_one('SELECT holder FROM session_turn_leases') is None
        db.release_session_turn_lease('stored', 'owner')


def test_external_noting_lifecycle_wakes_watcher_without_local_observers(tmp_path, monkeypatch):
    """Committed task-only changes wake another process, including the burst tail."""
    home, other = tmp_path / 'alex', tmp_path / 'other'
    home.mkdir(); other.mkdir()
    with SessionDB(home / 'state.db') as db, SessionDB(other / 'state.db') as foreign:
        for owner in (db, foreign):
            owner.create_session('same', source='desktop')
            owner.append_message('same', 'user', 'Evidence', message_uid='anchor')
        monkeypatch.setattr(server, '_watcher_home', lambda: other)
        monkeypatch.setattr(server, '_served_profile_homes', [home])
        before = server._sessions_sig()
        events = []
        monkeypatch.setattr(server, '_broadcast_global_event', lambda kind, payload: events.append((kind, payload)))
        monkeypatch.setattr(server, '_change_sigs', {'sessions.changed': before})
        monkeypatch.setattr(server, '_change_checked_at', {})
        monkeypatch.setattr(server, '_change_broadcast_at', {})
        monkeypatch.setattr(server, '_CHANGE_WATCHES', {'sessions.changed': (0.5, server._sessions_sig, lambda: {})})
        from secretary.web_events import subscribe, unsubscribe
        hints = []
        subscribe('external-noting-observer', lambda owner, ref, reason: hints.append((owner, ref, reason)))
        server._broadcast_watched_changes(now=98.0)
        script = '''import sys
from pathlib import Path
from hermes_state import SessionDB
from secretary.web_events import _observers, changed
assert not _observers
with SessionDB(Path(sys.argv[1])) as db:
    ref = db.resolve_conversation_ref('same')
    admission = db.noting_admit(ref, 'anchor', kind='idle')
    db.noting_child_register(admission, child_session_id='noting-child', profile='alex')
    print('started committed', flush=True)
    assert sys.stdin.readline().strip() == 'notify'
    changed(db, ref, 'task_started')
    print('started notified', flush=True)
    assert sys.stdin.readline().strip() == 'finish'
    db.noting_child_finish(admission, status='completed')
    print('finished committed', flush=True)
    assert sys.stdin.readline().strip() == 'notify'
    changed(db, ref, 'task_finished')
    print('finished notified', flush=True)
    assert sys.stdin.readline().strip() == 'exit'
'''
        child = subprocess.Popen([sys.executable, '-u', '-c', script, str(home / 'state.db')],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            assert child.stdout.readline().strip() == 'started committed'
            row = db._read_one('SELECT * FROM secretary_noting_task_children')
            assert row['status'] == 'running' and row['finished_at'] is None
            assert server._sessions_sig() == before
            assert not notification_path(home / 'state.db').exists()
            child.stdin.write('notify\n'); child.stdin.flush()
            assert child.stdout.readline().strip() == 'started notified'
            started = server._sessions_sig()
            assert started == before  # task-only writes leave transcript signals unchanged
            started_marker = secretary_notification_path(home / 'state.db').stat().st_mtime_ns
            server._broadcast_watched_changes(now=100.0)
            assert hints == [(home.resolve(), None, 'global_changed')]
            assert not [event for event in events if event[0] == 'sessions.changed']
            child.stdin.write('finish\n'); child.stdin.flush()
            assert child.stdout.readline().strip() == 'finished committed'
            row = db._read_one('SELECT * FROM secretary_noting_task_children')
            assert row['status'] == 'completed' and row['finished_at'] is not None
            assert server._sessions_sig() == started
            child.stdin.write('notify\n'); child.stdin.flush()
            assert child.stdout.readline().strip() == 'finished notified'
            finished = server._sessions_sig()
            assert finished == before
            assert secretary_notification_path(home / 'state.db').stat().st_mtime_ns != started_marker
            assert not notification_path(other / 'state.db').exists()
            assert foreign._read_one('SELECT * FROM secretary_noting_task_children') is None
            server._broadcast_watched_changes(now=100.6)
            assert hints == [(home.resolve(), None, 'global_changed')] * 2
            server._broadcast_watched_changes(now=102.1)
            assert hints == [(home.resolve(), None, 'global_changed')] * 2
            assert not [event for event in events if event[0] == 'sessions.changed']
            child.stdin.write('exit\n'); child.stdin.flush()
            _, error = child.communicate(timeout=15)
            assert child.returncode == 0, error
        finally:
            unsubscribe('external-noting-observer')
            if child.poll() is None:
                child.kill(); child.communicate(timeout=5)


@pytest.mark.parametrize('failure', ['write', 'unexpected'])
def test_secretary_signal_failure_preserves_local_owner_and_completion_metadata(tmp_path, monkeypatch, failure):
    from secretary.web_events import changed, subscribe, unsubscribe

    home = tmp_path / 'alex'
    home.mkdir()
    with SessionDB(home / 'state.db') as db:
        db.create_session('same', source='desktop')
        ref = db.resolve_conversation_ref('same')
        if failure == 'write':
            monkeypatch.setattr('hermes_state_history_notifications.secretary_notification_path', lambda _path: home)
        else:
            def fail(_db):
                raise RuntimeError('signal unavailable')
            monkeypatch.setattr('hermes_state_history_notifications.notify_secretary_changed', fail)
        legacy, modern = [], []
        subscribe('signal-legacy', lambda *args: legacy.append(args))
        subscribe('signal-modern', lambda *args, **metadata: modern.append((args, metadata)), include_metadata=True)
        try:
            assert changed(db, ref, 'notebook_changed', completion_snapshot_id='snapshot') is None
            expected = (home.resolve(), ref, 'notebook_changed')
            assert legacy == [expected]
            assert modern == [(expected, {'completion_snapshot_id': 'snapshot'})]
            assert db.get_session('same')['id'] == 'same'
        finally:
            unsubscribe('signal-legacy')
            unsubscribe('signal-modern')
        assert changed(db, ref, 'task_finished') is None
        assert db.get_session('same')['id'] == 'same'
