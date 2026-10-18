"""Frozen 07 Notebook function schemas; no runtime dependency on specification files."""

NOTEBOOK_MAINTAIN_SCHEMA = {'name': 'notebook_maintain',
 'description': "Create, update or archive one entry in this Noting task's working Notebook. Use the "
                'supplied full starting view and returned entries. Preserve source bodies while candidates '
                'aggregate references. Changes stay task-local until the runtime commits a Snapshot. Keep '
                'prose concise, without word quotas; never shorten IDs or remove necessary evidence. This '
                'tool never schedules reminders or writes external memory. create requires entry_type, '
                'fields and at least one valid provenance form; optional status/relations. update requires '
                'only entry_id and nonempty changes. archive requires only entry_id and reason. Do not mix '
                'parameters from different actions.',
 'parameters': {'type': 'object',
                'properties': {'action': {'type': 'string', 'enum': ['create', 'update', 'archive']},
                               'entry_type': {'type': 'string',
                                              'enum': ['matter',
                                                       'action',
                                                       'situation',
                                                       'implicit_gap',
                                                       'question',
                                                       'insight',
                                                       'decision',
                                                       'candidate'],
                                              'description': 'Create only. Fixed for the entry lifetime.'},
                               'entry_id': {'type': 'string',
                                            'description': 'Update/archive only. Use the stable ID from the '
                                                           'starting view or a successful result.'},
                               'fields': {'type': 'object',
                                          'properties': {'description': {'type': 'string',
                                                                         'description': 'A concise summary, '
                                                                                        'preferably one '
                                                                                        'sentence. Preserve '
                                                                                        'essential '
                                                                                        'qualifications; do '
                                                                                        'not copy the source '
                                                                                        'narrative.'},
                                                         'domains': {'type': 'array',
                                                                     'items': {'type': 'string'},
                                                                     'description': 'Optional short domain '
                                                                                    'or topic labels; not '
                                                                                    'additional entry '
                                                                                    'types.'},
                                                         'completion_condition': {'type': ['string', 'null'],
                                                                                  'description': 'What must '
                                                                                                 'be true '
                                                                                                 'for this '
                                                                                                 'matter or '
                                                                                                 'action to '
                                                                                                 'be '
                                                                                                 'complete '
                                                                                                 'or '
                                                                                                 'released.'},
                                                         'owner': {'type': ['string', 'null'],
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
                                                         'situation_ref': {'type': ['string', 'null'],
                                                                           'description': 'Stable entry_id '
                                                                                          'of the '
                                                                                          'corresponding '
                                                                                          'current '
                                                                                          'situation.'},
                                                         'missing_information': {'type': ['string', 'null'],
                                                                                 'description': 'The '
                                                                                                'specific '
                                                                                                'fact not '
                                                                                                'yet known; '
                                                                                                'no '
                                                                                                'speculative '
                                                                                                'explanations.'},
                                                         'impact': {'type': ['string', 'null'],
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
                                                         'certainty': {'type': ['string', 'null'],
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
                                                         'scope': {'type': ['string', 'null'],
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
                                                         'external_refs': {'type': 'array',
                                                                           'items': {'type': 'string'},
                                                                           'description': 'Exact existing '
                                                                                          'work-object, task '
                                                                                          'or Schedule '
                                                                                          'references; '
                                                                                          'references have '
                                                                                          'no state-changing '
                                                                                          'side effects.'},
                                                         'evidence_time': {'type': ['string', 'null'],
                                                                           'description': 'Time of the '
                                                                                          'original '
                                                                                          'substantive '
                                                                                          'evidence for the '
                                                                                          'indexed '
                                                                                          'information, '
                                                                                          'timezone-aware '
                                                                                          'ISO 8601; null '
                                                                                          'only if unknown.'},
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
                                                                           'description': 'Candidate only: stable current entry IDs for any target. Use these references or exact Message UIDs, never both; source bodies remain in place.'},
                                                         'targets': {'type': 'array',
                                                                     'items': {'type': 'string',
                                                                               'enum': ['memory', 'skill', 'rule', 'conversation']},
                                                                     'description': 'Candidate only: persistence destinations or Conversation working guidance. Main selects actual providers and write permissions.'},
                                                         'source_types': {'type': 'array',
                                                                          'items': {'type': 'string',
                                                                                    'enum': ['matter',
                                                                                             'action',
                                                                                             'situation',
                                                                                             'question',
                                                                                             'insight',
                                                                                             'decision']},
                                                                          'description': 'Candidate only: mapped source content types for notebook_refs; map implicit_gap to situation and preserve the union. Empty for direct Message sources.'},
                                                         'stage_evidence': {'type': ['string', 'null'],
                                                                            'description': 'Candidate only: brief evidence of proposal, approval or dispatch outcome; verify it against the original Conversation trajectory.'}},
                                          'required': [],
                                          'additionalProperties': False,
                                          'description': 'All types require description. Common optional fields: domains, external_refs, evidence_time, processing_note. Allowed type-specific fields (required unless marked optional): matter: completion_condition; optional blocker, last_progress_time. action: owner, completion_condition; optional blocker, last_progress_time. situation: subjects, time_context. implicit_gap: situation_ref, missing_information, impact, resolution_condition. question: unresolved_points; optional current_answer, last_discussion_time. insight: certainty, qualification. decision: scope, valid_when, ends_when; optional rationale. candidate: targets, notebook_refs, source_types; optional stage_evidence. Candidate uses either notebook_refs with mapped source_types or exact source_message_uids with both arrays empty; never both. Keep its description target-specific without repeating referenced bodies. Required text must be nonempty; express genuinely unknown conditions explicitly rather than inventing them. Optional single-valued fields may be cleared with null; arrays with []. Use only fields belonging to the entry type. For update, provide only changed properties; omitted properties remain. Keep prose concise, preferably one sentence per summary; no word or character quotas.'},
                               'status': {'type': 'string',
                                          'enum': ['in_progress',
                                                   'paused',
                                                   'completed',
                                                   'terminated',
                                                   'pending',
                                                   'waiting',
                                                   'open',
                                                   'answered',
                                                   'withdrawn',
                                                   'current',
                                                   'revised',
                                                   'active',
                                                   'superseded',
                                                   'revoked',
                                                   'expired',
                                                   'missing',
                                                   'resolved',
                                                   'invalid',
                                                   'proposed',
                                                   'awaiting_approval',
                                                   'approved',
                                                   'awaiting_result'],
                                          'description': 'States by entry_type (first is the default on '
                                                         'create): '
                                                         'matter=in_progress|paused|completed|terminated; '
                                                         'action=pending|in_progress|waiting|paused|completed|terminated; '
                                                         'situation=current|expired; '
                                                         'implicit_gap=missing|resolved|invalid; '
                                                         'question=open|answered|withdrawn; '
                                                         'insight=current|revised|withdrawn; '
                                                         'decision=active|superseded|revoked|expired; '
                                                         'candidate=proposed|awaiting_approval|approved|awaiting_result. '
                                                         'Use the evidence-supported target state; '
                                                         'corrections and reopening are allowed. A stage is '
                                                         'not approval or dispatch evidence by itself.'},
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
                                                                      'Notebook.'},
                               'source_time_range': {'anyOf': [{'type': 'object',
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
                                                               {'type': 'null'}],
                                                     'description': 'Current-Conversation evidence interval; supply both bounds together, or null to clear when other valid provenance remains. Not a Candidate source; keep null for Candidates.'},
                               'changes': {'type': 'object',
                                           'properties': {'fields': {'type': 'object',
                                                                     'properties': {'description': {'type': 'string',
                                                                                                    'description': 'A '
                                                                                                                   'concise '
                                                                                                                   'summary, '
                                                                                                                   'preferably '
                                                                                                                   'one '
                                                                                                                   'sentence. '
                                                                                                                   'Preserve '
                                                                                                                   'essential '
                                                                                                                   'qualifications; '
                                                                                                                   'do '
                                                                                                                   'not '
                                                                                                                   'copy '
                                                                                                                   'the '
                                                                                                                   'source '
                                                                                                                   'narrative.'},
                                                                                    'domains': {'type': 'array',
                                                                                                'items': {'type': 'string'},
                                                                                                'description': 'Optional '
                                                                                                               'short '
                                                                                                               'domain '
                                                                                                               'or '
                                                                                                               'topic '
                                                                                                               'labels; '
                                                                                                               'not '
                                                                                                               'additional '
                                                                                                               'entry '
                                                                                                               'types.'},
                                                                                    'completion_condition': {'type': ['string',
                                                                                                                      'null'],
                                                                                                             'description': 'What '
                                                                                                                            'must '
                                                                                                                            'be '
                                                                                                                            'true '
                                                                                                                            'for '
                                                                                                                            'this '
                                                                                                                            'matter '
                                                                                                                            'or '
                                                                                                                            'action '
                                                                                                                            'to '
                                                                                                                            'be '
                                                                                                                            'complete '
                                                                                                                            'or '
                                                                                                                            'released.'},
                                                                                    'owner': {'type': ['string',
                                                                                                       'null'],
                                                                                              'description': 'The '
                                                                                                             'evidenced '
                                                                                                             'person '
                                                                                                             'or '
                                                                                                             'agent '
                                                                                                             'responsible '
                                                                                                             'for '
                                                                                                             'the '
                                                                                                             'action; '
                                                                                                             'do '
                                                                                                             'not '
                                                                                                             'infer '
                                                                                                             'acceptance.'},
                                                                                    'blocker': {'type': ['string',
                                                                                                         'null'],
                                                                                                'description': 'The '
                                                                                                               'current '
                                                                                                               'concrete '
                                                                                                               'blocker, '
                                                                                                               'if '
                                                                                                               'any.'},
                                                                                    'subjects': {'type': 'array',
                                                                                                 'items': {'type': 'string'},
                                                                                                 'description': 'People, '
                                                                                                                'relationships '
                                                                                                                'or '
                                                                                                                'objects '
                                                                                                                'needed '
                                                                                                                'to '
                                                                                                                'understand '
                                                                                                                'a '
                                                                                                                'situation.'},
                                                                                    'time_context': {'type': ['string',
                                                                                                              'null'],
                                                                                                     'description': 'The '
                                                                                                                    'evidenced '
                                                                                                                    'event '
                                                                                                                    'time '
                                                                                                                    'or '
                                                                                                                    'temporal '
                                                                                                                    'context; '
                                                                                                                    'preserve '
                                                                                                                    'uncertainty.'},
                                                                                    'situation_ref': {'type': ['string',
                                                                                                               'null'],
                                                                                                      'description': 'Stable '
                                                                                                                     'entry_id '
                                                                                                                     'of '
                                                                                                                     'the '
                                                                                                                     'corresponding '
                                                                                                                     'current '
                                                                                                                     'situation.'},
                                                                                    'missing_information': {'type': ['string',
                                                                                                                     'null'],
                                                                                                            'description': 'The '
                                                                                                                           'specific '
                                                                                                                           'fact '
                                                                                                                           'not '
                                                                                                                           'yet '
                                                                                                                           'known; '
                                                                                                                           'no '
                                                                                                                           'speculative '
                                                                                                                           'explanations.'},
                                                                                    'impact': {'type': ['string',
                                                                                                        'null'],
                                                                                               'description': 'What '
                                                                                                              'present '
                                                                                                              'understanding '
                                                                                                              'or '
                                                                                                              'action '
                                                                                                              'depends '
                                                                                                              'on '
                                                                                                              'that '
                                                                                                              'missing '
                                                                                                              'fact.'},
                                                                                    'resolution_condition': {'type': ['string',
                                                                                                                      'null'],
                                                                                                             'description': 'What '
                                                                                                                            'evidence '
                                                                                                                            'would '
                                                                                                                            'supply '
                                                                                                                            'the '
                                                                                                                            'missing '
                                                                                                                            'fact.'},
                                                                                    'unresolved_points': {'type': ['string',
                                                                                                                   'null'],
                                                                                                          'description': 'The '
                                                                                                                         'remaining '
                                                                                                                         'question '
                                                                                                                         'actually '
                                                                                                                         'raised '
                                                                                                                         'or '
                                                                                                                         'engaged '
                                                                                                                         'with '
                                                                                                                         'by '
                                                                                                                         'the '
                                                                                                                         'user.'},
                                                                                    'current_answer': {'type': ['string',
                                                                                                                'null'],
                                                                                                       'description': 'The '
                                                                                                                      'supported '
                                                                                                                      'answer '
                                                                                                                      'or '
                                                                                                                      'progress; '
                                                                                                                      'do '
                                                                                                                      'not '
                                                                                                                      'invent '
                                                                                                                      'a '
                                                                                                                      'conclusion.'},
                                                                                    'certainty': {'type': ['string',
                                                                                                           'null'],
                                                                                                  'description': 'The '
                                                                                                                 "user's "
                                                                                                                 'actual '
                                                                                                                 'degree '
                                                                                                                 'of '
                                                                                                                 'certainty, '
                                                                                                                 'including '
                                                                                                                 'uncertainty.'},
                                                                                    'qualification': {'type': ['string',
                                                                                                               'null'],
                                                                                                      'description': 'Necessary '
                                                                                                                     'qualifications '
                                                                                                                     'or '
                                                                                                                     'scope '
                                                                                                                     'of '
                                                                                                                     'the '
                                                                                                                     "user's "
                                                                                                                     'understanding.'},
                                                                                    'scope': {'type': ['string',
                                                                                                       'null'],
                                                                                              'description': 'Where '
                                                                                                             'this '
                                                                                                             'user '
                                                                                                             'decision '
                                                                                                             'applies.'},
                                                                                    'valid_when': {'type': ['string',
                                                                                                            'null'],
                                                                                                   'description': 'Conditions '
                                                                                                                  'under '
                                                                                                                  'which '
                                                                                                                  'this '
                                                                                                                  'decision '
                                                                                                                  'remains '
                                                                                                                  'effective.'},
                                                                                    'ends_when': {'type': ['string',
                                                                                                           'null'],
                                                                                                  'description': 'The '
                                                                                                                 'evidenced '
                                                                                                                 'condition '
                                                                                                                 'ending '
                                                                                                                 'its '
                                                                                                                 'effect; '
                                                                                                                 'unknown '
                                                                                                                 'is '
                                                                                                                 'permitted '
                                                                                                                 'when '
                                                                                                                 'genuinely '
                                                                                                                 'unspecified.'},
                                                                                    'rationale': {'type': ['string',
                                                                                                           'null'],
                                                                                                  'description': 'Only '
                                                                                                                 'the '
                                                                                                                 'decisive, '
                                                                                                                 'evidenced '
                                                                                                                 'reason; '
                                                                                                                 'keep '
                                                                                                                 'it '
                                                                                                                 'brief.'},
                                                                                    'external_refs': {'type': 'array',
                                                                                                      'items': {'type': 'string'},
                                                                                                      'description': 'Exact '
                                                                                                                     'existing '
                                                                                                                     'work-object, '
                                                                                                                     'task '
                                                                                                                     'or '
                                                                                                                     'Schedule '
                                                                                                                     'references; '
                                                                                                                     'references '
                                                                                                                     'have '
                                                                                                                     'no '
                                                                                                                     'state-changing '
                                                                                                                     'side '
                                                                                                                     'effects.'},
                                                                                    'evidence_time': {'type': ['string',
                                                                                                               'null'],
                                                                                                      'description': 'Time '
                                                                                                                     'of '
                                                                                                                     'the '
                                                                                                                     'original '
                                                                                                                     'substantive '
                                                                                                                     'evidence '
                                                                                                                     'for '
                                                                                                                     'the '
                                                                                                                     'indexed '
                                                                                                                     'information, '
                                                                                                                     'timezone-aware '
                                                                                                                     'ISO '
                                                                                                                     '8601; '
                                                                                                                     'null '
                                                                                                                     'only '
                                                                                                                     'if '
                                                                                                                     'unknown.'},
                                                                                    'last_progress_time': {'type': ['string',
                                                                                                                    'null'],
                                                                                                           'description': 'Last '
                                                                                                                          'evidenced '
                                                                                                                          'substantive '
                                                                                                                          'progress '
                                                                                                                          'of '
                                                                                                                          'a '
                                                                                                                          'matter/action, '
                                                                                                                          'not '
                                                                                                                          'a '
                                                                                                                          'read '
                                                                                                                          'or '
                                                                                                                          'rewrite '
                                                                                                                          'time.'},
                                                                                    'last_discussion_time': {'type': ['string',
                                                                                                                      'null'],
                                                                                                             'description': 'Last '
                                                                                                                            'substantive '
                                                                                                                            'user '
                                                                                                                            'discussion '
                                                                                                                            'of '
                                                                                                                            'this '
                                                                                                                            'question.'},
                                                                                    'processing_note': {'type': ['string',
                                                                                                                 'null'],
                                                                                                        'description': 'Brief '
                                                                                                                       'concrete '
                                                                                                                       'disposition '
                                                                                                                       'and '
                                                                                                                       'reason '
                                                                                                                       'from '
                                                                                                                       'this '
                                                                                                                       'processing '
                                                                                                                       'pass; '
                                                                                                                       'not '
                                                                                                                       'a '
                                                                                                                       'running '
                                                                                                                       'diary.'},
                                                                                    'notebook_refs': {'type': 'array',
                                                                                                      'items': {'type': 'string'},
                                                                                                      'description': 'Candidate only: stable current entry IDs for any target. Use these references or exact Message UIDs, never both; source bodies remain in place.'},
                                                                                    'targets': {'type': 'array',
                                                                                                'items': {'type': 'string',
                                                                                                          'enum': ['memory', 'skill', 'rule', 'conversation']},
                                                                                                'description': 'Candidate only: persistence destinations or Conversation working guidance. Main selects actual providers and write permissions.'},
                                                                                    'source_types': {'type': 'array',
                                                                                                     'items': {'type': 'string',
                                                                                                               'enum': ['matter',
                                                                                                                        'action',
                                                                                                                        'situation',
                                                                                                                        'question',
                                                                                                                        'insight',
                                                                                                                        'decision']},
                                                                                                     'description': 'Candidate only: mapped source content types for notebook_refs; map implicit_gap to situation and preserve the union. Empty for direct Message sources.'},
                                                                                    'stage_evidence': {'type': ['string',
                                                                                                                'null'],
                                                                                                       'description': 'Candidate only: brief evidence of proposal, approval or dispatch outcome; verify it against the original Conversation trajectory.'}},
                                                                     'required': [],
                                                                     'additionalProperties': False,
                                                                     'description': 'All types require description. Common optional fields: domains, external_refs, evidence_time, processing_note. Allowed type-specific fields (required unless marked optional): matter: completion_condition; optional blocker, last_progress_time. action: owner, completion_condition; optional blocker, last_progress_time. situation: subjects, time_context. implicit_gap: situation_ref, missing_information, impact, resolution_condition. question: unresolved_points; optional current_answer, last_discussion_time. insight: certainty, qualification. decision: scope, valid_when, ends_when; optional rationale. candidate: targets, notebook_refs, source_types; optional stage_evidence. Candidate uses either notebook_refs with mapped source_types or exact source_message_uids with both arrays empty; never both. Keep its description target-specific without repeating referenced bodies. Required text must be nonempty; express genuinely unknown conditions explicitly rather than inventing them. Optional single-valued fields may be cleared with null; arrays with []. Use only fields belonging to the entry type. For update, provide only changed properties; omitted properties remain. Keep prose concise, preferably one sentence per summary; no word or character quotas.'},
                                                          'status': {'type': 'string',
                                                                     'enum': ['in_progress',
                                                                              'paused',
                                                                              'completed',
                                                                              'terminated',
                                                                              'pending',
                                                                              'waiting',
                                                                              'open',
                                                                              'answered',
                                                                              'withdrawn',
                                                                              'current',
                                                                              'revised',
                                                                              'active',
                                                                              'superseded',
                                                                              'revoked',
                                                                              'expired',
                                                                              'missing',
                                                                              'resolved',
                                                                              'invalid',
                                                                              'proposed',
                                                                              'awaiting_approval',
                                                                              'approved',
                                                                              'awaiting_result'],
                                                                     'description': 'States by entry_type '
                                                                                    '(first is the default '
                                                                                    'on create): '
                                                                                    'matter=in_progress|paused|completed|terminated; '
                                                                                    'action=pending|in_progress|waiting|paused|completed|terminated; '
                                                                                    'situation=current|expired; '
                                                                                    'implicit_gap=missing|resolved|invalid; '
                                                                                    'question=open|answered|withdrawn; '
                                                                                    'insight=current|revised|withdrawn; '
                                                                                    'decision=active|superseded|revoked|expired; '
                                                                                    'candidate=proposed|awaiting_approval|approved|awaiting_result. '
                                                                                    'Use the '
                                                                                    'evidence-supported '
                                                                                    'target state; '
                                                                                    'corrections and '
                                                                                    'reopening are allowed. '
                                                                                    'A stage is not approval '
                                                                                    'or dispatch evidence by '
                                                                                    'itself.'},
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
                                                                                  'required': ['kind',
                                                                                               'entry_id'],
                                                                                  'additionalProperties': False},
                                                                        'description': 'Only real current '
                                                                                       'relationships; send '
                                                                                       'the complete '
                                                                                       'replacement array.'},
                                                          'source_message_uids': {'type': 'array',
                                                                                  'items': {'type': 'string'},
                                                                                  'description': 'Exact '
                                                                                                 'supporting '
                                                                                                 'Message '
                                                                                                 'UIDs in '
                                                                                                 'this '
                                                                                                 'Conversation. '
                                                                                                 'Send the '
                                                                                                 'complete '
                                                                                                 'replacement '
                                                                                                 'array; '
                                                                                                 'Conversation '
                                                                                                 'ownership '
                                                                                                 'is '
                                                                                                 'supplied '
                                                                                                 'by the '
                                                                                                 'bound '
                                                                                                 'Notebook.'},
                                                          'source_time_range': {'anyOf': [{'type': 'object',
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
                                                                                           'required': ['start_time',
                                                                                                        'end_time'],
                                                                                           'additionalProperties': False},
                                                                                          {'type': 'null'}],
                                                                                'description': 'Current-Conversation evidence interval; supply both bounds together, or null to clear when other valid provenance remains. Not a Candidate source; keep null for Candidates.'}},
                                           'required': [],
                                           'additionalProperties': False},
                               'reason': {'type': 'string',
                                          'description': 'Archive only. Prefer one sentence explaining the '
                                                         'concrete disposition and evidence; do not write '
                                                         'only "processed".'}},
                'required': ['action'],
                'additionalProperties': False}}

NOTEBOOK_SHOW_SCHEMA = {'name': 'notebook_show',
 'description': 'Read the complete current Notebook for your bound Conversation. Main receives the current '
                "effective committed Snapshot; Noting receives its own task's current working view, "
                'including successful uncommitted changes. Read when the supplied view is missing or when '
                'you need to inspect the complete current state, relationships or candidate aggregation. The '
                'runtime selects the view from caller identity; no scope selector is accepted. Does not '
                'retrieve archived entries, publish changes or write external memory. Do not expand all '
                'provenance merely because a Notebook is returned.',
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
