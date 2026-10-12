import { beforeEach, expect, it, vi } from 'vitest'
import { createGatewayEventHandler } from '../app/createGatewayEventHandler.js'
import { resetOverlayState } from '../app/overlayStore.js'
import { resetTurnState, getTurnState } from '../app/turnStore.js'
import { resetUiState, patchUiState, getUiState } from '../app/uiStore.js'
import type { Msg } from '../types.js'
import { toTranscriptMessages } from '../domain/messages.js'

const buildCtx = (appended: Msg[]) =>
  ({
    composer: { dequeue: () => undefined, queueEditRef: { current: null }, sendQueued: vi.fn(), setInput: vi.fn() },
    gateway: { gw: { request: vi.fn(async () => null) }, rpc: vi.fn(async () => null) },
    session: {
      STARTUP_RESUME_ID: '',
      colsRef: { current: 80 },
      newSession: vi.fn(),
      resetSession: vi.fn(),
      resumeById: vi.fn(),
      setCatalog: vi.fn()
    },
    submission: { submitRef: { current: vi.fn() } },
    system: { bellOnComplete: false, sys: vi.fn() },
    transcript: { appendMessage: (msg: Msg) => appended.push(msg), panel: vi.fn(), setHistoryItems: vi.fn() },
    voice: { setProcessing: vi.fn(), setRecording: vi.fn(), setVoiceEnabled: vi.fn() }
  }) as any

beforeEach(() => {
  resetOverlayState()
  resetTurnState()
  resetUiState()
})

it('keeps each committed Framework in the timeline while idle and across the next turn', () => {
  const appended: Msg[] = []
  const ctx = buildCtx(appended)
  const onEvent = createGatewayEventHandler(ctx)
  const bodies = ['Background: notebook updated at T. Processed memo entries have been cleared.', '派发正文']

  patchUiState({ busy: false, status: 'ready' })
  for (const text of bodies) {
    onEvent({ type: 'status.update', payload: { kind: 'framework', text } } as any)
  }
  expect(appended).toEqual(bodies.map(text => ({ kind: 'event', role: 'system', text })))
  const cold = toTranscriptMessages(
    bodies.map(text => ({
      role: 'user',
      text: '<framework-message>\n' + text + '\n</framework-message>',
      display_kind: 'process_complete',
      display_metadata: { display_text: text }
    }))
  )
  expect(cold).toEqual(appended)
  expect(ctx.system.sys).not.toHaveBeenCalled()
  expect(getUiState().status).toBe('ready')
  expect(getTurnState().activity).toEqual([])
  onEvent({ type: 'message.start' } as any)
  expect(appended.map(row => row.text)).toEqual(bodies)
  expect(ctx.submission.submitRef.current).not.toHaveBeenCalled()
})
