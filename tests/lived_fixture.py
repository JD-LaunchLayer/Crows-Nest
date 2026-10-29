"""A synthetic, well-populated life used to measure context pressure.

It is not Crow's real history. It imitates the volume and shape of a save that
has been running for weeks, including the repeated woodland-reading loop.
"""
import random


def populate(state, seed=7):
    rng = random.Random(seed)
    topics = ['woodland plant interactions', 'carving a bowl', 'spring water', 'tree felling',
              'the reading cabin roof', 'star positions', 'fruit bushes', 'stone stacking']
    mem_id = 1
    memories = []
    for i in range(500):
        topic = topics[i % len(topics)]
        kind = 'started' if i % 2 == 0 else 'experience'
        text = ('Started ' + rng.choice(['read', 'craft', 'explore', 'observe']) + '.') if kind == 'started' else \
            f'Finished a session about {topic}; noticed detail number {i} about texture, light and timing.'
        memories.append({'id': mem_id, 'at': f'2026-10-{1 + i // 30:02d}T{(i % 24):02d}:00:00+01:00', 'day': 1 + i // 30,
                         'time': '10:00', 'event': text, 'reason': f'I wanted to understand {topic} better because of an earlier attempt.',
                         'kind': kind, 'action': 'read', 'intention': f'Understand {topic}'})
        mem_id += 1
    state['memories'] = memories
    state['next_memory_id'] = mem_id
    state['long_term'] = [{'source_id': 20 + i * 3, 'fact': f'Finished a session about {topics[i % len(topics)]}.',
                           'interpretation': f'Lesson {i}: concrete examples help with {topics[i % len(topics)]}; '
                                             'the excerpt did not answer the specific question.',
                           'at': '2026-10-10T10:00:00+01:00'} for i in range(120)]
    # One genuinely useful, old, specific lesson that recency-only retrieval will miss.
    state['long_term'][5] = {'source_id': 37, 'fact': 'Carved a bowl with deep passes across the grain.',
                             'interpretation': 'Deep passes across the grain split the bowl rim; light passes along the grain held.',
                             'at': '2026-10-02T10:00:00+01:00'}
    state['personality_notes'] = [{'text': f'I may prefer {t} when I am rested.', 'source_id': 10 + i, 'at': ''}
                                  for i, t in enumerate(topics[:12] + topics[:4])][-12:]
    state['interests'] = {t: round(rng.uniform(-3, 8), 2) for t in topics + ['archaeology', 'woodland period', 'light',
                                                                          'roofs', 'stars', 'water', 'grain', 'tools']}
    state['wishes'] = [{'id': i + 1, 'text': f'A field guide to {t}', 'reason': 'Wikipedia excerpts were too general.',
                        'day': 3, 'last_day': 9, 'mentions': 4, 'status': 'expressed', 'at': '', 'context': []}
                       for i, t in enumerate(topics[:5])]
    state['projects'] = [{'id': i + 1, 'title': f'Understand {t} through repeated sessions', 'status': 'paused' if i else 'active',
                          'target_action': 'read', 'target': 5, 'progress': 2, 'created': ''} for i, t in enumerate(topics[:4])]
    state['current_intention'] = 'Carve a bowl whose rim does not split'
    state['next_step'] = 'Try the bowl again with a method that held before'
    state['appraisals'] = [{'at': '', 'source_id': 30 + i, 'feeling': 'Mildly frustrated that the excerpt was off-topic.',
                            'topic': 'woodland reading', 'enjoyment': 0, 'meaning': 'My question remains unanswered.',
                            'concern': 'Understand woodland plant interactions', 'valence': -0.2, 'importance': 0.4}
                           for i in range(60)]
    log = []
    for i in range(40):
        log.append({'id': 40 + i, 'at': '', 'title': 'Woodland period' if i % 3 else 'Plant ecology',
                    'url': 'https://en.wikipedia.org/wiki/Woodland_period' if i % 3 else 'https://en.wikipedia.org/wiki/Plant_ecology',
                    'query': 'woodland plant interactions', 'question': 'How do woodland plants interact with each other?',
                    'intention': 'Understand woodland plant interactions', 'reason': '', 'mode': 'lookup',
                    'status': 'processed', 'summary': 'The excerpt describes pre-Columbian North American cultures, not plants.',
                    'lesson': '', 'answer_status': 'not_answered', 'next_step': '', 'processed_chars': 2500,
                    'fingerprint': 'a' if i % 3 else 'b', 'new_source_text': i < 2})
    state['reading_log'] = log
    state['research_feedback'] = [{'query': 'woodland plants', 'question': 'How do plants interact?',
                                   'reason': 'Only archaeology candidates were found.'} for _ in range(6)]
    state['materials'] = 4
    return state
