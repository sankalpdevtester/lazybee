// Cloudflare Worker - LeetCode Proxy
// Deploy at workers.cloudflare.com (free)
export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': '*' } })
    }

    const secret = request.headers.get('X-Proxy-Secret')
    if (secret !== (env.PROXY_SECRET || 'lazybee_proxy_2026')) {
      return new Response('Unauthorized', { status: 401 })
    }

    let body
    try { body = await request.json() } catch { return new Response('Bad Request', { status: 400 }) }

    const { url, method, headers, data } = body
    if (!url || !url.includes('leetcode.com')) {
      return new Response('Forbidden', { status: 403 })
    }

    const resp = await fetch(url, {
      method: method || 'POST',
      headers: { ...headers },
      body: data ? JSON.stringify(data) : undefined,
    })

    const text = await resp.text()
    return new Response(text, {
      status: resp.status,
      headers: { 'Content-Type': resp.headers.get('Content-Type') || 'application/json', 'Access-Control-Allow-Origin': '*' },
    })
  }
}
