"""Secretary slash adapters for the existing messaging command/main-Turn paths."""

from hermes_cli.cli_secretary_commands import notebook_command, noting_command, propose_persistence_command, secretary_feedback_messages


class GatewaySecretaryCommandsMixin:
    async def _secretary_command_for_event(self, event, command, *, session_id=None):
        if session_id is None:
            entry = await self.async_session_store.get_or_create_session(event.source)
            session_id = entry.session_id
        store = self._session_db
        db = getattr(store, "_db", None) if store is not None else None
        kwargs = {"source": event.source.platform.value} if command in (notebook_command, noting_command) else {}
        return await self._run_in_executor_with_context(
            lambda: command(db, session_id, event.get_command_args() or "", **kwargs))

    async def _handle_secretary_feedback(self, event, command):
        entry = await self.async_session_store.get_or_create_session(event.source)
        session_id = entry.session_id
        result = await self._secretary_command_for_event(event, command, session_id=session_id)
        timestamp = getattr(event, "timestamp", None)
        if hasattr(timestamp, "timestamp"):
            timestamp = timestamp.timestamp()
        for message in secretary_feedback_messages(event.text, result.output, timestamp=timestamp):
            await self.async_session_store.append_to_transcript(session_id, message)
        return result.output

    async def _handle_notebook_command(self, event):
        return await self._handle_secretary_feedback(event, notebook_command)

    async def _handle_noting_command(self, event):
        return await self._handle_secretary_feedback(event, noting_command)

    async def _hm_cmd_propose_persistence(self, event, source, quick_key):
        # The same profile binding as ordinary Slash handlers; this path falls through to the
        # existing main Turn after replacing its user prompt, never enqueues a child/worker.
        async with self._async_profile_scope_for_source(source):
            result = await self._secretary_command_for_event(event, propose_persistence_command)
        if not result.prompt:
            return True, result.output
        event.text = result.prompt
        return False, None
