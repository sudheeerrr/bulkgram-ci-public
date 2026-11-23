import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createSyntheticServer, validateCatalog } from '../src/server.mjs';

const fixture = JSON.parse(await readFile(new URL('../fixtures/catalogue.json', import.meta.url), 'utf8'));
async function request(path, method='GET') {
  const server=createSyntheticServer(fixture);
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try {
    const {port}=server.address();
    const response=await fetch(`http://127.0.0.1:${port}${path}`,{method,signal:AbortSignal.timeout(5000)});
    return {status:response.status, headers:response.headers, data:await response.json()};
  } finally {await new Promise((resolve,reject)=>server.close(err=>err?reject(err):resolve()));}
}

test('synthetic fixture is tightly validated',()=>assert.equal(validateCatalog(fixture).length,3));
test('duplicate IDs rejected',()=>assert.throws(()=>validateCatalog([...fixture.slice(0,2),fixture[0]]),TypeError));
test('unexpected private contact field rejected',()=>assert.throws(()=>validateCatalog(fixture.map((x,i)=>i===0?{...x,phone:'fake'}:x)),TypeError));
test('invalid ID rejected',()=>assert.throws(()=>validateCatalog(fixture.map((x,i)=>i===0?{...x,id:'-3'}:x)),TypeError));
test('health identifies fixture as synthetic',async()=>assert.deepEqual((await request('/health')).data,{status:'ok',synthetic:true}));
test('catalogue returns synthetic records',async()=>assert.equal((await request('/catalogue')).data.products.length,3));
test('category filter limits records',async()=>assert.equal((await request('/catalogue?category=home')).data.products.length,1));
test('unknown category rejected',async()=>assert.equal((await request('/catalogue?category=admin')).status,400));
test('unexpected query rejected',async()=>assert.equal((await request('/catalogue?token=secret')).status,400));
test('duplicate filters rejected',async()=>assert.equal((await request('/catalogue?category=home&category=packaging')).status,400));
test('POST forbidden',async()=>assert.equal((await request('/catalogue','POST')).status,405));
test('private endpoints never exposed',async()=>assert.equal((await request('/admin')).status,404));
test('public response sets defensive headers',async()=>{
  const r=await request('/catalogue');assert.equal(r.headers.get('cache-control'),'no-store');
  assert.equal(r.headers.get('x-content-type-options'),'nosniff');
});
