# The API reference's SDK tab: embedding the interview in a page.
SDK_TAB = """# SDK

Your page can show the interview itself, for a candidate invited with `sign_in` false. Your
server invites them and passes the `invite_url` to your page, which embeds it with prepza's
script; never put your API key in a page. The page must be on one of your company's allowed
domains (below) and served over HTTPS: anywhere else the interview isn't shown.

```html
<div id="interview"></div>
<script>
  // Calls made before the script has loaded wait for it.
  window.Prepza = window.Prepza || { q: [], embed: function (o) { this.q.push(o) } }
  // The candidate's invite_url, which your server got when it invited them.
  const candidateInviteUrl = "https://prepza.ai/invite/3fTq9xLk2VbN7wZr8YcP1mHd5sJ4gAe6uQo0RiKtEy"
  Prepza.embed({
    element: "#interview",
    url: candidateInviteUrl,
    theme: "dark",
    title: "Interview",
    onReady: () => {},
    onStart: () => {},
    onFinish: ({ candidateId }) => {},
    onError: ({ code }) => {},
  })
</script>
<script async src="https://prepza.ai/embed/v1.js"></script>
```

`theme` is optional: `"light"` or `"dark"` always shows the interview in that theme, in your
company's colors for it (set on the company's **brand** tab); `"default"`, or none, the
candidate's own theme, or the one the invite asked for. `title` names the frame for screen
readers. The frame fits its height to the interview. `onFinish` gets the candidate's `id`, so
your page can take them on; their results come with the `candidate.finished` web hook as usual.
`onError` gets a `code`: `"timeout"` when the frame didn't load within 20 seconds (the page isn't
on an allowed domain, or the network failed), `"invite_unavailable"` when the link expired or
was revoked, `"load_failed"` when it couldn't be read (try again). Loaded without `async`, the
script is ready at once and `Prepza.embed(...)` returns `{ destroy() }`, which removes the frame.
While the interview runs, the candidate should stay on it: leaving it, including for the rest of
your page, is recorded as a page leave.

If your site sends a Content-Security-Policy, allow `script-src https://prepza.ai` and
`frame-src https://prepza.ai`. Don't add an `integrity` attribute: `v1.js` gets fixes in place
(cached for 5 minutes), so a pinned hash would stop it loading; it is served over HTTPS and may
be loaded with `crossorigin="anonymous"`. Within `v1`, options, callbacks and `onError` codes are
only ever added; a change that isn't compatible would come as `v2.js`, with `v1.js` kept working.

## Allowed domains

The sites that may embed your interviews, which an owner or admin lists on the API page's SDK
tab: a domain like `jobs.acme.com` allows that site, `*.acme.com` every subdomain of `acme.com`
(add `acme.com` too for the domain itself). Pages must be served over HTTPS. To try it on your
own computer, allow localhost on the same tab, or add `localhost` (any port) or `localhost:3000`
to the list; localhost is refused until you do. The domains are only for embedding: the API and
web hooks don't use them (a key is limited by its allowed IPs), and a `return_url` may be any
https address.

## Changes to v1

- 2026-10-29: the page must be on one of the company's allowed domains (localhost when allowed),
  instead of its verified website domain.
- 2026-10-20: `onError`, `title`, calls queued before the script loads, and a console warning for
  an option it doesn't know.
"""
