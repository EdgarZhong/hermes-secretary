"""Notebook v2 fixed function schemas; no runtime dependency on specification files."""

NOTEBOOK_CREATE_SCHEMA = {'name': 'notebook_create',
 'description': "Create one entry in this Noting task's working Notebook. Use the entry type's documented "
                'fields and supporting provenance. Record enough content for Main to understand the matter, '
                'situation or discussion and its current relevance. Use the entry_id returned by a '
                'successful call for later edits. Returned evidence time is derived and read-only. This tool '
                'does not create or change a Schedule.',
 'parameters': {'type': 'object',
                'properties': {'entry_type': {'type': 'string',
                                              'enum': ['matter',
                                                       'action',
                                                       'situation',
                                                       'implicit_gap',
                                                       'question',
                                                       'insight',
                                                       'decision',
                                                       'candidate'],
                                              'description': 'Create only. Fixed for the entry lifetime.'},
                               'fields': {'type': 'object',
                                          'properties': {'description': {'type': 'string',
                                                                         'description': 'A concise semantic '
                                                                                        'index: the specific '
                                                                                        'subject, current '
                                                                                        'significance and '
                                                                                        'useful outcomes, '
                                                                                        'conditions or '
                                                                                        'uncertainty. Keep '
                                                                                        'enough content for '
                                                                                        'Main to understand '
                                                                                        'the entry; detailed '
                                                                                        'source material '
                                                                                        'remains in '
                                                                                        'conversation_history.'},
                                                         'domains': {'type': 'array',
                                                                     'items': {'type': 'string'},
                                                                     'description': 'Optional short domain '
                                                                                    'or topic labels; not '
                                                                                    'additional entry '
                                                                                    'types.'},
                                                         'completion_condition': {'type': 'string',
                                                                                  'description': 'What must '
                                                                                                 'be true '
                                                                                                 'for this '
                                                                                                 'matter or '
                                                                                                 'action to '
                                                                                                 'be '
                                                                                                 'complete '
                                                                                                 'or '
                                                                                                 'released.'},
                                                         'owner': {'type': 'string',
                                                                   'description': 'The evidenced person or '
                                                                                  'agent responsible for the '
                                                                                  'action; do not infer '
                                                                                  'acceptance.'},
                                                         'blocker': {'type': ['string', 'null'],
                                                                     'description': 'The current concrete '
                                                                                    'blocker, if any.'},
                                                         'subjects': {'type': 'array',
                                                                      'items': {'type': 'string'},
                                                                      'description': 'People, relationships '
                                                                                     'or objects needed to '
                                                                                     'understand a '
                                                                                     'situation.'},
                                                         'time_context': {'type': ['string', 'null'],
                                                                          'description': 'The evidenced '
                                                                                         'event time or '
                                                                                         'temporal context; '
                                                                                         'preserve '
                                                                                         'uncertainty.'},
                                                         'situation_ref': {'type': 'string',
                                                                           'description': 'Stable entry_id '
                                                                                          'of the '
                                                                                          'corresponding '
                                                                                          'current '
                                                                                          'situation.'},
                                                         'missing_information': {'type': 'string',
                                                                                 'description': 'The '
                                                                                                'specific '
                                                                                                'fact not '
                                                                                                'yet known; '
                                                                                                'no '
                                                                                                'speculative '
                                                                                                'explanations.'},
                                                         'impact': {'type': 'string',
                                                                    'description': 'What present '
                                                                                   'understanding or action '
                                                                                   'depends on that missing '
                                                                                   'fact.'},
                                                         'resolution_condition': {'type': ['string', 'null'],
                                                                                  'description': 'What '
                                                                                                 'evidence '
                                                                                                 'would '
                                                                                                 'supply the '
                                                                                                 'missing '
                                                                                                 'fact.'},
                                                         'unresolved_points': {'type': ['string', 'null'],
                                                                               'description': 'The remaining '
                                                                                              'question '
                                                                                              'actually '
                                                                                              'raised or '
                                                                                              'engaged with '
                                                                                              'by the user.'},
                                                         'current_answer': {'type': ['string', 'null'],
                                                                            'description': 'The supported '
                                                                                           'answer or '
                                                                                           'progress; do not '
                                                                                           'invent a '
                                                                                           'conclusion.'},
                                                         'certainty': {'type': 'string',
                                                                       'description': "The user's actual "
                                                                                      'degree of certainty, '
                                                                                      'including '
                                                                                      'uncertainty.'},
                                                         'qualification': {'type': ['string', 'null'],
                                                                           'description': 'Necessary '
                                                                                          'qualifications or '
                                                                                          'scope of the '
                                                                                          "user's "
                                                                                          'understanding.'},
                                                         'scope': {'type': 'string',
                                                                   'description': 'Where this user decision '
                                                                                  'applies.'},
                                                         'valid_when': {'type': ['string', 'null'],
                                                                        'description': 'Conditions under '
                                                                                       'which this decision '
                                                                                       'remains effective.'},
                                                         'ends_when': {'type': ['string', 'null'],
                                                                       'description': 'The evidenced '
                                                                                      'condition ending its '
                                                                                      'effect; unknown is '
                                                                                      'permitted when '
                                                                                      'genuinely '
                                                                                      'unspecified.'},
                                                         'rationale': {'type': ['string', 'null'],
                                                                       'description': 'Only the decisive, '
                                                                                      'evidenced reason; '
                                                                                      'keep it brief.'},
                                                         'last_progress_time': {'type': ['string', 'null'],
                                                                                'description': 'Last '
                                                                                               'evidenced '
                                                                                               'substantive '
                                                                                               'progress of '
                                                                                               'a '
                                                                                               'matter/action, '
                                                                                               'not a read '
                                                                                               'or rewrite '
                                                                                               'time.'},
                                                         'last_discussion_time': {'type': ['string', 'null'],
                                                                                  'description': 'Last '
                                                                                                 'substantive '
                                                                                                 'user '
                                                                                                 'discussion '
                                                                                                 'of this '
                                                                                                 'question.'},
                                                         'processing_note': {'type': ['string', 'null'],
                                                                             'description': 'Brief concrete '
                                                                                            'disposition and '
                                                                                            'reason from '
                                                                                            'this processing '
                                                                                            'pass; not a '
                                                                                            'running diary.'},
                                                         'notebook_refs': {'type': 'array',
                                                                           'items': {'type': 'string'},
                                                                           'description': 'Candidate only: '
                                                                                          'stable current '
                                                                                          'entry IDs for any '
                                                                                          'target. Use these '
                                                                                          'references or '
                                                                                          'direct Message '
                                                                                          'UIDs/time ranges, never both; '
                                                                                          'source bodies '
                                                                                          'remain in place.'},
                                                         'targets': {'type': 'array',
                                                                     'items': {'type': 'string',
                                                                               'enum': ['memory',
                                                                                        'skill',
                                                                                        'rule',
                                                                                        'conversation']},
                                                                     'description': 'Candidate only: '
                                                                                    'persistence '
                                                                                    'destinations or '
                                                                                    'Conversation working '
                                                                                    'guidance. Main selects '
                                                                                    'actual providers and '
                                                                                    'write permissions.'},
                                                         'source_types': {'type': 'array',
                                                                          'items': {'type': 'string',
                                                                                    'enum': ['matter',
                                                                                             'action',
                                                                                             'situation',
                                                                                             'question',
                                                                                             'insight',
                                                                                             'decision']},
                                                                          'description': 'Candidate only: '
                                                                                         'mapped source '
                                                                                         'content types for '
                                                                                         'notebook_refs; map '
                                                                                         'implicit_gap to '
                                                                                         'situation and '
                                                                                         'preserve the '
                                                                                         'union. Empty for '
                                                                                         'direct Message '
                                                                                         'sources.'},
                                                         'stage_evidence': {'type': ['string', 'null'],
                                                                            'description': 'Candidate only: '
                                                                                           'brief evidence '
                                                                                           'of proposal, '
                                                                                           'approval or '
                                                                                           'dispatch '
                                                                                           'outcome; verify '
                                                                                           'it against the '
                                                                                           'original '
                                                                                           'Conversation '
                                                                                           'trajectory.'}},
                                          'required': ['description'],
                                          'additionalProperties': False,
                                          'description': 'All types require description. Common optional '
                                                         'fields: domains, processing_note. '
                                                         'Required/optional fields by type: matter: '
                                                         'completion_condition; optional blocker, '
                                                         'last_progress_time. action: owner, '
                                                         'completion_condition; optional blocker, '
                                                         'last_progress_time. situation: subjects; optional '
                                                         'time_context. implicit_gap: situation_ref, '
                                                         'missing_information, impact; optional '
                                                         'resolution_condition. question: description only; '
                                                         'optional unresolved_points, current_answer, '
                                                         'last_discussion_time. insight: certainty; optional '
                                                         'qualification. decision: scope; optional '
                                                         'valid_when, ends_when, rationale. candidate: '
                                                         'targets, notebook_refs, source_types; optional '
                                                         'stage_evidence. Candidate uses either '
                                                         'notebook_refs with mapped source_types and empty '
                                                         'direct sources, or source_message_uids and/or '
                                                         'source_time_ranges with notebook_refs/source_types '
                                                         'empty; never mix the two modes. Use only fields '
                                                         'belonging to the entry type. '
                                                         'Required text must be nonempty; do not invent '
                                                         'facts to fill it. Optional single-valued fields '
                                                         'may be cleared with null; arrays with []. On '
                                                         'update, fields merges by property and omitted '
                                                         'properties remain. Returned evidence_time is '
                                                         'runtime-derived, read-only; do not supply on '
                                                         'create or update.'},
                               'done': {'type': 'boolean',
                                        'description': 'True only when available evidence confirms this entry is concluded; '
                                                       'concluded does not mean successful. False means conclusion is not '
                                                       'confirmed, not that work has not started. Create defaults to false; '
                                                       'omitted on update keeps the current value. Record progress, outcome '
                                                       'and reasons in the semantic fields. Does not archive an entry or '
                                                       'grant approval, write permission or settlement.'},
                               'relations': {'type': 'array',
                                             'items': {'type': 'object',
                                                       'properties': {'kind': {'type': 'string',
                                                                               'enum': ['part_of',
                                                                                        'depends_on',
                                                                                        'based_on',
                                                                                        'supersedes',
                                                                                        'related_to']},
                                                                      'entry_id': {'type': 'string',
                                                                                   'description': 'Stable '
                                                                                                  'current '
                                                                                                  'Notebook '
                                                                                                  'entry '
                                                                                                  'ID.'}},
                                                       'required': ['kind', 'entry_id'],
                                                       'additionalProperties': False},
                                             'description': 'Only real current relationships; send the '
                                                            'complete replacement array.'},
                               'source_message_uids': {'type': 'array',
                                                       'items': {'type': 'string'},
                                                       'description': 'Exact supporting Message UIDs in this '
                                                                      'Conversation. Send the complete '
                                                                      'replacement array; Conversation '
                                                                      'ownership is supplied by the bound '
                                                                      'Notebook. For content entries and '
                                                                      'direct-source Candidates, Message UIDs and '
                                                                      'source_time_ranges may be supplied '
                                                                      'together; retain the sources '
                                                                      'supporting the recorded content.'},
                               'schedule_suggestion': {'anyOf': [{'type': 'object',
                                                                  'properties': {'content': {'type': 'string',
                                                                                             'description': 'Semantic '
                                                                                                            'advice: '
                                                                                                            'a '
                                                                                                            'self-contained '
                                                                                                            'proposed '
                                                                                                            'Schedule '
                                                                                                            'delivery '
                                                                                                            'body, '
                                                                                                            'including '
                                                                                                            'necessary '
                                                                                                            'background, '
                                                                                                            'subject, '
                                                                                                            'action '
                                                                                                            'and '
                                                                                                            'conditions.'},
                                                                                 'schedule': {'type': 'string',
                                                                                              'description': 'Semantic '
                                                                                                             'timing '
                                                                                                             'or '
                                                                                                             'recurrence '
                                                                                                             'advice '
                                                                                                             'in '
                                                                                                             'ordinary '
                                                                                                             'text. '
                                                                                                             'This '
                                                                                                             'is '
                                                                                                             'not '
                                                                                                             'parsed '
                                                                                                             'or '
                                                                                                             'validated '
                                                                                                             'as '
                                                                                                             'Scheduler '
                                                                                                             'time '
                                                                                                             'syntax.'}},
                                                                  'required': ['content', 'schedule'],
                                                                  'additionalProperties': False},
                                                                 {'type': 'null'}],
                                                       'description': 'At most one suggestion per entry; '
                                                                      'replace this entire object, or use '
                                                                      'null to clear it. Advice for Main, '
                                                                      'not ready-to-submit Scheduler '
                                                                      'arguments or evidence of '
                                                                      'registration. This tool does not '
                                                                      'create or update Schedules.'},
                               'source_time_ranges': {'type': 'array',
                                                      'items': {'type': 'object',
                                                                'properties': {'start_time': {'type': 'string',
                                                                                              'description': 'Inclusive '
                                                                                                             'timezone-aware '
                                                                                                             'ISO '
                                                                                                             '8601 '
                                                                                                             'timestamp.'},
                                                                               'end_time': {'type': 'string',
                                                                                            'description': 'Inclusive '
                                                                                                           'timezone-aware '
                                                                                                           'ISO '
                                                                                                           '8601 '
                                                                                                           'timestamp.'}},
                                                                'required': ['start_time', 'end_time'],
                                                                'additionalProperties': False},
                                                      'description': 'Complete replacement array of evidence '
                                                                     'intervals in this bound Conversation. '
                                                                     'Each element requires timezone-aware '
                                                                     'start_time and end_time; equal bounds '
                                                                     'express one instant. Use [] to clear; '
                                                                     'omit to keep unchanged on update. The '
                                                                     'content entries and direct-source '
                                                                     'Candidates may combine these '
                                                                     'intervals with source_message_uids. '
                                                                     'Every source must be available on the '
                                                                     'authorized path. Candidates use either '
                                                                     'direct Message UIDs/time ranges with '
                                                                     'notebook_refs/source_types empty, or '
                                                                     'notebook_refs with mapped source_types '
                                                                     'and both direct-source arrays empty.'}},
                'required': ['entry_type', 'fields'],
                'additionalProperties': False}}

NOTEBOOK_UPDATE_SCHEMA = {'name': 'notebook_update',
 'description': "Update one existing entry in this Noting task's working Notebook. Supply entry_id and only "
                'the attributes to change, directly as tool parameters. fields merges by property; each '
                'supplied array replaces the complete array. Preserve still-relevant content and its '
                'sources. Keep the same subject and entry type; create a separate entry for a different '
                'matter. entry_id, entry_type and returned evidence time cannot be edited. Supply at least '
                'one changed attribute besides entry_id. Optional singleton null clears the value; '
                'schedule_suggestion replaces the whole object or null clears it.',
 'parameters': {'type': 'object',
                'properties': {'entry_id': {'type': 'string',
                                            'description': 'Update/archive only. Use the stable ID from the '
                                                           'starting view or a successful result.'},
                               'fields': {'type': 'object',
                                          'properties': {'description': {'type': 'string',
                                                                         'description': 'A concise semantic '
                                                                                        'index: the specific '
                                                                                        'subject, current '
                                                                                        'significance and '
                                                                                        'useful outcomes, '
                                                                                        'conditions or '
                                                                                        'uncertainty. Keep '
                                                                                        'enough content for '
                                                                                        'Main to understand '
                                                                                        'the entry; detailed '
                                                                                        'source material '
                                                                                        'remains in '
                                                                                        'conversation_history.'},
                                                         'domains': {'type': 'array',
                                                                     'items': {'type': 'string'},
                                                                     'description': 'Optional short domain '
                                                                                    'or topic labels; not '
                                                                                    'additional entry '
                                                                                    'types.'},
                                                         'completion_condition': {'type': 'string',
                                                                                  'description': 'What must '
                                                                                                 'be true '
                                                                                                 'for this '
                                                                                                 'matter or '
                                                                                                 'action to '
                                                                                                 'be '
                                                                                                 'complete '
                                                                                                 'or '
                                                                                                 'released.'},
                                                         'owner': {'type': 'string',
                                                                   'description': 'The evidenced person or '
                                                                                  'agent responsible for the '
                                                                                  'action; do not infer '
                                                                                  'acceptance.'},
                                                         'blocker': {'type': ['string', 'null'],
                                                                     'description': 'The current concrete '
                                                                                    'blocker, if any.'},
                                                         'subjects': {'type': 'array',
                                                                      'items': {'type': 'string'},
                                                                      'description': 'People, relationships '
                                                                                     'or objects needed to '
                                                                                     'understand a '
                                                                                     'situation.'},
                                                         'time_context': {'type': ['string', 'null'],
                                                                          'description': 'The evidenced '
                                                                                         'event time or '
                                                                                         'temporal context; '
                                                                                         'preserve '
                                                                                         'uncertainty.'},
                                                         'situation_ref': {'type': 'string',
                                                                           'description': 'Stable entry_id '
                                                                                          'of the '
                                                                                          'corresponding '
                                                                                          'current '
                                                                                          'situation.'},
                                                         'missing_information': {'type': 'string',
                                                                                 'description': 'The '
                                                                                                'specific '
                                                                                                'fact not '
                                                                                                'yet known; '
                                                                                                'no '
                                                                                                'speculative '
                                                                                                'explanations.'},
                                                         'impact': {'type': 'string',
                                                                    'description': 'What present '
                                                                                   'understanding or action '
                                                                                   'depends on that missing '
                                                                                   'fact.'},
                                                         'resolution_condition': {'type': ['string', 'null'],
                                                                                  'description': 'What '
                                                                                                 'evidence '
                                                                                                 'would '
                                                                                                 'supply the '
                                                                                                 'missing '
                                                                                                 'fact.'},
                                                         'unresolved_points': {'type': ['string', 'null'],
                                                                               'description': 'The remaining '
                                                                                              'question '
                                                                                              'actually '
                                                                                              'raised or '
                                                                                              'engaged with '
                                                                                              'by the user.'},
                                                         'current_answer': {'type': ['string', 'null'],
                                                                            'description': 'The supported '
                                                                                           'answer or '
                                                                                           'progress; do not '
                                                                                           'invent a '
                                                                                           'conclusion.'},
                                                         'certainty': {'type': 'string',
                                                                       'description': "The user's actual "
                                                                                      'degree of certainty, '
                                                                                      'including '
                                                                                      'uncertainty.'},
                                                         'qualification': {'type': ['string', 'null'],
                                                                           'description': 'Necessary '
                                                                                          'qualifications or '
                                                                                          'scope of the '
                                                                                          "user's "
                                                                                          'understanding.'},
                                                         'scope': {'type': 'string',
                                                                   'description': 'Where this user decision '
                                                                                  'applies.'},
                                                         'valid_when': {'type': ['string', 'null'],
                                                                        'description': 'Conditions under '
                                                                                       'which this decision '
                                                                                       'remains effective.'},
                                                         'ends_when': {'type': ['string', 'null'],
                                                                       'description': 'The evidenced '
                                                                                      'condition ending its '
                                                                                      'effect; unknown is '
                                                                                      'permitted when '
                                                                                      'genuinely '
                                                                                      'unspecified.'},
                                                         'rationale': {'type': ['string', 'null'],
                                                                       'description': 'Only the decisive, '
                                                                                      'evidenced reason; '
                                                                                      'keep it brief.'},
                                                         'last_progress_time': {'type': ['string', 'null'],
                                                                                'description': 'Last '
                                                                                               'evidenced '
                                                                                               'substantive '
                                                                                               'progress of '
                                                                                               'a '
                                                                                               'matter/action, '
                                                                                               'not a read '
                                                                                               'or rewrite '
                                                                                               'time.'},
                                                         'last_discussion_time': {'type': ['string', 'null'],
                                                                                  'description': 'Last '
                                                                                                 'substantive '
                                                                                                 'user '
                                                                                                 'discussion '
                                                                                                 'of this '
                                                                                                 'question.'},
                                                         'processing_note': {'type': ['string', 'null'],
                                                                             'description': 'Brief concrete '
                                                                                            'disposition and '
                                                                                            'reason from '
                                                                                            'this processing '
                                                                                            'pass; not a '
                                                                                            'running diary.'},
                                                         'notebook_refs': {'type': 'array',
                                                                           'items': {'type': 'string'},
                                                                           'description': 'Candidate only: '
                                                                                          'stable current '
                                                                                          'entry IDs for any '
                                                                                          'target. Use these '
                                                                                          'references or '
                                                                                          'direct Message '
                                                                                          'UIDs/time ranges, never both; '
                                                                                          'source bodies '
                                                                                          'remain in place.'},
                                                         'targets': {'type': 'array',
                                                                     'items': {'type': 'string',
                                                                               'enum': ['memory',
                                                                                        'skill',
                                                                                        'rule',
                                                                                        'conversation']},
                                                                     'description': 'Candidate only: '
                                                                                    'persistence '
                                                                                    'destinations or '
                                                                                    'Conversation working '
                                                                                    'guidance. Main selects '
                                                                                    'actual providers and '
                                                                                    'write permissions.'},
                                                         'source_types': {'type': 'array',
                                                                          'items': {'type': 'string',
                                                                                    'enum': ['matter',
                                                                                             'action',
                                                                                             'situation',
                                                                                             'question',
                                                                                             'insight',
                                                                                             'decision']},
                                                                          'description': 'Candidate only: '
                                                                                         'mapped source '
                                                                                         'content types for '
                                                                                         'notebook_refs; map '
                                                                                         'implicit_gap to '
                                                                                         'situation and '
                                                                                         'preserve the '
                                                                                         'union. Empty for '
                                                                                         'direct Message '
                                                                                         'sources.'},
                                                         'stage_evidence': {'type': ['string', 'null'],
                                                                            'description': 'Candidate only: '
                                                                                           'brief evidence '
                                                                                           'of proposal, '
                                                                                           'approval or '
                                                                                           'dispatch '
                                                                                           'outcome; verify '
                                                                                           'it against the '
                                                                                           'original '
                                                                                           'Conversation '
                                                                                           'trajectory.'}},
                                          'required': [],
                                          'additionalProperties': False,
                                          'description': 'All types require description. Common optional '
                                                         'fields: domains, processing_note. '
                                                         'Required/optional fields by type: matter: '
                                                         'completion_condition; optional blocker, '
                                                         'last_progress_time. action: owner, '
                                                         'completion_condition; optional blocker, '
                                                         'last_progress_time. situation: subjects; optional '
                                                         'time_context. implicit_gap: situation_ref, '
                                                         'missing_information, impact; optional '
                                                         'resolution_condition. question: description only; '
                                                         'optional unresolved_points, current_answer, '
                                                         'last_discussion_time. insight: certainty; optional '
                                                         'qualification. decision: scope; optional '
                                                         'valid_when, ends_when, rationale. candidate: '
                                                         'targets, notebook_refs, source_types; optional '
                                                         'stage_evidence. Candidate uses either '
                                                         'notebook_refs with mapped source_types and empty '
                                                         'direct sources, or source_message_uids and/or '
                                                         'source_time_ranges with notebook_refs/source_types '
                                                         'empty; never mix the two modes. Use only fields '
                                                         'belonging to the entry type. '
                                                         'Required text must be nonempty; do not invent '
                                                         'facts to fill it. Optional single-valued fields '
                                                         'may be cleared with null; arrays with []. On '
                                                         'update, fields merges by property and omitted '
                                                         'properties remain. Returned evidence_time is '
                                                         'runtime-derived, read-only; do not supply on '
                                                         'create or update.'},
                               'done': {'type': 'boolean',
                                        'description': 'True only when available evidence confirms this entry is concluded; '
                                                       'concluded does not mean successful. False means conclusion is not '
                                                       'confirmed, not that work has not started. Create defaults to false; '
                                                       'omitted on update keeps the current value. Record progress, outcome '
                                                       'and reasons in the semantic fields. Does not archive an entry or '
                                                       'grant approval, write permission or settlement.'},
                               'relations': {'type': 'array',
                                             'items': {'type': 'object',
                                                       'properties': {'kind': {'type': 'string',
                                                                               'enum': ['part_of',
                                                                                        'depends_on',
                                                                                        'based_on',
                                                                                        'supersedes',
                                                                                        'related_to']},
                                                                      'entry_id': {'type': 'string',
                                                                                   'description': 'Stable '
                                                                                                  'current '
                                                                                                  'Notebook '
                                                                                                  'entry '
                                                                                                  'ID.'}},
                                                       'required': ['kind', 'entry_id'],
                                                       'additionalProperties': False},
                                             'description': 'Only real current relationships; send the '
                                                            'complete replacement array.'},
                               'source_message_uids': {'type': 'array',
                                                       'items': {'type': 'string'},
                                                       'description': 'Exact supporting Message UIDs in this '
                                                                      'Conversation. Send the complete '
                                                                      'replacement array; Conversation '
                                                                      'ownership is supplied by the bound '
                                                                      'Notebook. For content entries and '
                                                                      'direct-source Candidates, Message UIDs and '
                                                                      'source_time_ranges may be supplied '
                                                                      'together; retain the sources '
                                                                      'supporting the recorded content.'},
                               'schedule_suggestion': {'anyOf': [{'type': 'object',
                                                                  'properties': {'content': {'type': 'string',
                                                                                             'description': 'Semantic '
                                                                                                            'advice: '
                                                                                                            'a '
                                                                                                            'self-contained '
                                                                                                            'proposed '
                                                                                                            'Schedule '
                                                                                                            'delivery '
                                                                                                            'body, '
                                                                                                            'including '
                                                                                                            'necessary '
                                                                                                            'background, '
                                                                                                            'subject, '
                                                                                                            'action '
                                                                                                            'and '
                                                                                                            'conditions.'},
                                                                                 'schedule': {'type': 'string',
                                                                                              'description': 'Semantic '
                                                                                                             'timing '
                                                                                                             'or '
                                                                                                             'recurrence '
                                                                                                             'advice '
                                                                                                             'in '
                                                                                                             'ordinary '
                                                                                                             'text. '
                                                                                                             'This '
                                                                                                             'is '
                                                                                                             'not '
                                                                                                             'parsed '
                                                                                                             'or '
                                                                                                             'validated '
                                                                                                             'as '
                                                                                                             'Scheduler '
                                                                                                             'time '
                                                                                                             'syntax.'}},
                                                                  'required': ['content', 'schedule'],
                                                                  'additionalProperties': False},
                                                                 {'type': 'null'}],
                                                       'description': 'At most one suggestion per entry; '
                                                                      'replace this entire object, or use '
                                                                      'null to clear it. Advice for Main, '
                                                                      'not ready-to-submit Scheduler '
                                                                      'arguments or evidence of '
                                                                      'registration. This tool does not '
                                                                      'create or update Schedules.'},
                               'source_time_ranges': {'type': 'array',
                                                      'items': {'type': 'object',
                                                                'properties': {'start_time': {'type': 'string',
                                                                                              'description': 'Inclusive '
                                                                                                             'timezone-aware '
                                                                                                             'ISO '
                                                                                                             '8601 '
                                                                                                             'timestamp.'},
                                                                               'end_time': {'type': 'string',
                                                                                            'description': 'Inclusive '
                                                                                                           'timezone-aware '
                                                                                                           'ISO '
                                                                                                           '8601 '
                                                                                                           'timestamp.'}},
                                                                'required': ['start_time', 'end_time'],
                                                                'additionalProperties': False},
                                                      'description': 'Complete replacement array of evidence '
                                                                     'intervals in this bound Conversation. '
                                                                     'Each element requires timezone-aware '
                                                                     'start_time and end_time; equal bounds '
                                                                     'express one instant. Use [] to clear; '
                                                                     'omit to keep unchanged on update. The '
                                                                     'content entries and direct-source '
                                                                     'Candidates may combine these '
                                                                     'intervals with source_message_uids. '
                                                                     'Every source must be available on the '
                                                                     'authorized path. Candidates use either '
                                                                     'direct Message UIDs/time ranges with '
                                                                     'notebook_refs/source_types empty, or '
                                                                     'notebook_refs with mapped source_types '
                                                                     'and both direct-source arrays empty.'}},
                'required': ['entry_id'],
                'minProperties': 2,
                'additionalProperties': False}}

NOTEBOOK_ARCHIVE_SCHEMA = {'name': 'notebook_archive',
 'description': 'Archive one entry that no longer needs to remain in the current working Notebook. Supply '
                'its entry_id and a concrete reason. Preserve needed content and repair incoming '
                'source/situation references first. Auxiliary relations are removed atomically; the receipt '
                "names affected entries. Apply this task's retention and settlement rules: remove confirmed "
                'successfully dispatched scope, preserving only later changes, unfinished responsibilities '
                'or other pending proposal needs not settled by that write. This tool does not delete '
                'original Conversation messages.',
 'parameters': {'type': 'object',
                'properties': {'entry_id': {'type': 'string',
                                            'description': 'Update/archive only. Use the stable ID from the '
                                                           'starting view or a successful result.'},
                               'reason': {'type': 'string',
                                          'description': 'Archive only. Prefer one sentence explaining the '
                                                         'concrete disposition and evidence; do not write '
                                                         'only "processed".'}},
                'required': ['entry_id', 'reason'],
                'additionalProperties': False}}

NOTEBOOK_SHOW_SCHEMA = {'name': 'notebook_show',
 'description': 'Read the complete current Notebook for your bound Conversation. Main receives the current '
                "effective committed Snapshot; Noting receives its own task's current working view, "
                'including successful uncommitted changes. Read when the supplied view is missing or when '
                'you need to inspect the complete current state, relationships or candidate aggregation. The '
                'runtime selects the view from caller identity; no scope selector is accepted. Does not '
                'retrieve archived entries, publish changes or write external memory. Do not expand all '
                'provenance merely because a Notebook is returned. Returned evidence_time is '
                'runtime-derived, read-only; do not supply it on create or update.',
 'parameters': {'type': 'object', 'properties': {}, 'required': [], 'additionalProperties': False}}

FINISH_NOTING_SCHEMA = {'name': 'finish_noting',
 'description': 'Request completion after all Noting responsibilities have been considered and the working '
                'Notebook is consistent. Call this as the final, standalone tool action, then stop. The '
                'runtime commits the Snapshot after the native Turn returns; this result is not a commit '
                'receipt.',
 'parameters': {'type': 'object',
                'properties': {'reason': {'type': 'string',
                                          'description': 'Briefly state concrete changes, archives, '
                                                         'candidates, settlements and unresolved '
                                                         'limitations, or why no change was needed. Do not '
                                                         'repeat the full Notebook.'}},
                'required': ['reason'],
                'additionalProperties': False}}
