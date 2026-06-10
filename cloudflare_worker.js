// Cloudflare Worker - LeetCode Submit Proxy
// Deploy at: workers.cloudflare.com (free tier)
// This forwards LeetCode requests through Cloudflare's IP (not blocked by LC)

export default {
  async fetch(request, env) {
    // Only allow POST requests with correct secret
    const secret = request.headers.get('X-Proxy-Secret')
    if (secret !== env.PROXY_SECRET) {
      return new Response('Unauthorized', { status: 401 })
    }

    const body = await request.json()
    const { url, method, headers, data } = body

    // Only allow leetcode.com URLs
    if (!url.includes('leetcode.com')) {
      return new Response('Forbidden', { status: 403 })
    }

    const resp = await fetch(url, {
      method: method || 'POST',
      headers: headers,
      body: data ? JSON.stringify(data) : undefined,
    })

    const text = await resp.text()
    return new Response(text, {
      status: resp.status,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}
