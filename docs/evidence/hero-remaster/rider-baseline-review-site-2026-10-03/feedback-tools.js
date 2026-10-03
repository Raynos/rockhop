// Optional page tools use the same browser-local notes as the visible fields.
if (document.modelContext?.registerTool) {
  const lifecycle = new AbortController();
  window.addEventListener('pagehide', () => lifecycle.abort(), { once: true });
  const register = tool => {
    try {
      Promise.resolve(document.modelContext.registerTool(tool, {
        signal: lifecycle.signal,
      })).catch(() => {});
    } catch {}
  };
  register({
    name: 'read_picture_feedback',
    description: 'Read the picture names and feedback saved in this browser.',
    inputSchema: { type: 'object', properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, untrustedContentHint: true },
    execute() {
      return [...document.querySelectorAll('#pictures article')].map(article => ({
        id: article.querySelector('textarea').dataset.id,
        title: article.querySelector('h2').textContent,
        feedback: article.querySelector('textarea').value,
      }));
    },
  });
  register({
    name: 'save_picture_feedback',
    description: 'Save picture feedback in this browser and update the note fields.',
    inputSchema: {
      type: 'object',
      properties: {
        entries: {
          type: 'array',
          items: {
            type: 'object',
            properties: { id: { type: 'string' }, feedback: { type: 'string' } },
            required: ['id', 'feedback'],
            additionalProperties: false,
          },
        },
      },
      required: ['entries'],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    execute(input) {
      if (!input || !Array.isArray(input.entries) ||
          Object.keys(input).some(key => key !== 'entries')) {
        throw Error('Expected picture feedback entries.');
      }
      const fields = new Map([...document.querySelectorAll('textarea')]
        .map(field => [field.dataset.id, field]));
      for (const entry of input.entries) {
        if (!entry || typeof entry.id !== 'string' ||
            typeof entry.feedback !== 'string' || !fields.has(entry.id) ||
            Object.keys(entry).some(key => !['id', 'feedback'].includes(key))) {
          throw Error('Invalid picture feedback.');
        }
      }
      for (const entry of input.entries) {
        const field = fields.get(entry.id);
        field.value = entry.feedback;
        field.dispatchEvent(new Event('input', { bubbles: true }));
      }
      return { updated: input.entries.length, storage: 'this browser' };
    },
  });
}
