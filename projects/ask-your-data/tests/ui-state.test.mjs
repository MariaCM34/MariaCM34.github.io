import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

test('unsupported question clears evidence from a previous successful result', async () => {
  class Element {
    constructor() { this.textContent=''; this.value=''; this.hidden=false; this.children=[]; this.events={}; this.classList={toggle(){},remove(){}}; this.style={}; }
    addEventListener(name,callback) { this.events[name]=callback; }
    setAttribute() {}
    replaceChildren(...children) { this.children=children; }
    append(...children) { this.children.push(...children); }
  }
  const elements=new Map();
  const get=id => { if(!elements.has(id)) elements.set(id,new Element()); return elements.get(id); };
  get('start').value='2026-01-01';
  get('end').value='2026-03-31';
  const originalDocument=globalThis.document;
  const originalFetch=globalThis.fetch;
  globalThis.document={getElementById:get,createElement:()=>new Element(),documentElement:{lang:'en'},title:''};
  globalThis.fetch=async()=>({ok:true,json:async()=>JSON.parse(readFileSync(new URL('../data/orders.json',import.meta.url),'utf8'))});
  try {
    await import(`../app.js?ui-state=${Date.now()}`);
    get('suggestion-list').children[0].events.click();
    assert.match(get('sql').textContent,/SELECT month/);
    assert.equal(get('scanned').textContent,'17 / 17');
    get('question').value='Tell me a joke';
    get('query-form').events.submit({preventDefault(){}});
    assert.match(get('message').textContent,/Unsupported question/);
    assert.equal(get('result').hidden,true);
    assert.equal(get('sql').textContent,'Select a supported question to see its template.');
    for(const id of ['scanned','excluded','filter']) assert.equal(get(id).textContent,'—');
  } finally {
    globalThis.document=originalDocument;
    globalThis.fetch=originalFetch;
  }
});
