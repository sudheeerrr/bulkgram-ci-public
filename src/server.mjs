import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';

const path = new URL('../fixtures/catalogue.json', import.meta.url);
const CATEGORIES = new Set(['packaging', 'home', 'stationery']);

export function validateCatalog(raw) {
  if (!Array.isArray(raw) || raw.length !== 3) throw new TypeError('Synthetic fixture must contain exactly three products');
  const ids = new Set();
  for (const item of raw) {
    if (!item || typeof item !== 'object' || !/^[1-9][0-9]{0,14}$/.test(item.id) ||
        typeof item.name !== 'string' || item.name.length > 80 ||
        !CATEGORIES.has(item.category) || !Number.isSafeInteger(item.stock) || item.stock < 0 ||
        ids.has(item.id) || Object.keys(item).sort().join(',') !== 'category,id,name,stock') {
      throw new TypeError('Invalid synthetic catalogue record');
    }
    ids.add(item.id);
  }
  return raw.map((item) => Object.freeze({...item}));
}

export function createSyntheticServer(catalogue) {
  const records = validateCatalog(catalogue);
  return createServer((req, res) => {
    const headers = { 'cache-control': 'no-store', 'x-content-type-options': 'nosniff',
      'content-security-policy': "default-src 'none'", 'referrer-policy': 'no-referrer' };
    const send = (status, body) => {
      res.writeHead(status, {'content-type': 'application/json; charset=utf-8', ...headers});
      res.end(JSON.stringify(body));
    };
    if (req.method !== 'GET') return send(405, {error:'method_not_allowed'});
    let url;
    try {url = new URL(req.url, 'http://localhost');} catch {return send(400,{error:'bad_url'});}
    if (url.pathname === '/health' && !url.search) return send(200, {status:'ok', synthetic:true});
    if (url.pathname !== '/catalogue') return send(404,{error:'not_found'});
    if ([...url.searchParams.keys()].some((key) => key !== 'category') || url.searchParams.getAll('category').length > 1) {
      return send(400,{error:'invalid_filter'});
    }
    const category = url.searchParams.get('category');
    if (category !== null && !CATEGORIES.has(category)) return send(400,{error:'invalid_filter'});
    return send(200,{synthetic:true,products:category ? records.filter(p=>p.category===category) : records});
  });
}

if (process.argv[1] && new URL('file://' + process.argv[1]).href === import.meta.url) {
  const records = JSON.parse(await readFile(path,'utf8'));
  const host='127.0.0.1';
  const port=Number(process.env.PORT || 8765);
  if (!Number.isSafeInteger(port) || port < 1 || port > 65535) throw new RangeError('Invalid PORT');
  const server=createSyntheticServer(records);
  server.listen(port,host,()=>console.log(`Synthetic fixture server bound to ${host}:${port}`));
}
