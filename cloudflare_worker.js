// Cloudflare Worker - LeetCode Proxy
// This worker handles TWO things:
// 1. /proxy - forwards LeetCode API requests (submissions, checks) from CF edge IP
// 2. /login - logs into LeetCode from CF edge IP and returns fresh session cookies
//
// IMPORTANT: You must login via /login ONCE to get cookies bound to CF's IP.
// Then use those cookies in Render env vars. CF edge IPs are stable per region.
//
// Deploy at workers.cloudflare.com (free)

export default {
  async fetch(request, env) {
    const url = new URL(request.url)

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, GET',
          'Access-Control-Allow-Headers': '*',
        },
      })
    }

    // Auth check
    const secret = request.headers.get('X-Proxy-Secret')
    const expectedSecret = env.PROXY_SECRET || 'lazybee_proxy_2026'
    if (secret !== expectedSecret) {
      return new Response('Unauthorized', { status: 401 })
    }

    // Route: /login — get fresh LeetCode session from CF edge IP
    if (url.pathname.endsWith('/login')) {
      return handleLogin(request, env)
    }

    // Route: default — proxy LeetCode requests
    return handleProxy(request, env)
  },
}

async function handleLogin(request, env) {
  // Read credentials from worker env vars: LC_USERNAME and LC_PASSWORD
  const username = env.LC_USERNAME
  const password = env.LC_PASSWORD

  if (!username || !password) {
    return new Response(JSON.stringify({ error: 'LC_USERNAME and LC_PASSWORD not set in worker env vars' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    })
  }

  try {
    // Step 1: GET login page to get initial csrftoken
    const loginPageResp = await fetch('https://leetcode.com/accounts/login/', {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
      redirect: 'follow',
    })

    // Extract csrftoken from Set-Cookie
    const initCookies = loginPageResp.headers.get('set-cookie') || ''
    const csrfMatch = initCookies.match(/csrftoken=([^;]+)/)
    const initCsrf = csrfMatch ? csrfMatch[1] : ''

    if (!initCsrf) {
      return new Response(JSON.stringify({ error: 'Could not get initial CSRF token', cookies: initCookies }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    // Step 2: POST login with credentials
    const loginResp = await fetch('https://leetcode.com/accounts/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': `csrftoken=${initCsrf}`,
        'x-csrftoken': initCsrf,
        'Referer': 'https://leetcode.com/accounts/login/',
        'Origin': 'https://leetcode.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
      body: new URLSearchParams({
        login: username,
        password: password,
        csrfmiddlewaretoken: initCsrf,
        next: '/problemset/',
      }).toString(),
      redirect: 'manual', // don't follow — we want the cookies from the redirect response
    })

    const loginCookies = loginResp.headers.get('set-cookie') || ''
    const sessionMatch = loginCookies.match(/LEETCODE_SESSION=([^;]+)/)
    const csrfNewMatch = loginCookies.match(/csrftoken=([^;]+)/)

    const newSession = sessionMatch ? sessionMatch[1] : ''
    const newCsrf = csrfNewMatch ? csrfNewMatch[1] : ''

    if (!newSession) {
      return new Response(JSON.stringify({
        error: 'Login failed — no LEETCODE_SESSION in response',
        status: loginResp.status,
        cookies: loginCookies,
      }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    }

    return new Response(JSON.stringify({
      success: true,
      LEETCODE_SESSION: newSession,
      LEETCODE_CSRF: newCsrf,
      message: 'Copy these values to Render env vars. These cookies are bound to Cloudflare edge IP.',
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}

async function handleProxy(request, env) {
  let body
  try {
    body = await request.json()
  } catch {
    return new Response('Bad Request', { status: 400 })
  }

  const { url, method, headers, data } = body

  if (!url || !url.includes('leetcode.com')) {
    return new Response('Forbidden', { status: 403 })
  }

  const fetchInit = {
    method: method || 'POST',
    headers: { ...headers },
    redirect: 'follow',
  }

  if (method !== 'GET' && data) {
    fetchInit.body = JSON.stringify(data)
  }

  try {
    const resp = await fetch(url, fetchInit)
    const text = await resp.text()

    const responseHeaders = {
      'Content-Type': resp.headers.get('Content-Type') || 'application/json',
      'Access-Control-Allow-Origin': '*',
    }

    const setCookie = resp.headers.get('set-cookie')
    if (setCookie) responseHeaders['set-cookie'] = setCookie

    return new Response(text, {
      status: resp.status,
      headers: responseHeaders,
    })
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}
