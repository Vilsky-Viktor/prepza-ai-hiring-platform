/*
 * prepza embed, v1: a candidate's interview inside your own site.
 *
 *   <div id="interview"></div>
 *   <script async src="https://prepza.ai/embed/v1.js"></script>
 *   <script>
 *     // Calls made before the script has loaded wait for it.
 *     window.Prepza = window.Prepza || { q: [], embed: function (o) { this.q.push(o) } }
 *     Prepza.embed({
 *       element: "#interview",
 *       // The invite_url your server got from POST /v1/interviews/{id}/candidates.
 *       url: "https://prepza.ai/invite/3fTq9xLk2VbN7wZr8YcP1mHd5sJ4gAe6uQo0RiKtEy",
 *       // Optional: "light" or "dark" always shows that theme, in your company's colors for it;
 *       // "default" (or none) the candidate's own.
 *       theme: "dark",
 *       // Optional: the frame's name for screen readers.
 *       title: "Interview",
 *       onReady: () => {},
 *       onStart: () => {},
 *       onFinish: ({ candidateId }) => {},
 *       // "timeout": the frame didn't load (not your verified domain, or the network);
 *       // "invite_unavailable": the link expired or was revoked; "load_failed": try again.
 *       onError: ({ code }) => {},
 *     })
 *   </script>
 *
 * Only a candidate invited with sign_in false, and only on your company's verified website
 * domain (and its subdomains): anywhere else the frame stays empty and onError says "timeout".
 * Within v1, options, callbacks and messages are only ever added.
 */
;(function () {
  "use strict"

  var VERSION = 1
  var SOURCE = "prepza"
  var MIN_HEIGHT = 640
  // How long the frame has to say it's ready before onError({ code: "timeout" }).
  var READY_TIMEOUT_MS = 20000
  var OPTIONS = [
    "element",
    "url",
    "theme",
    "title",
    "onReady",
    "onStart",
    "onFinish",
    "onError",
  ]
  var existing = window.Prepza

  // Included twice: the first copy stays.
  if (existing && existing.version) {
    return
  }

  // prepza's address, where this copy was loaded from. An element named "currentScript" on the
  // page shadows document.currentScript (DOM clobbering), which would send the frame, and the
  // invite's link, elsewhere: only a real script element counts; anything else is prepza.ai.
  var current = document.currentScript
  var ORIGIN =
    current instanceof HTMLScriptElement
      ? new URL(current.src).origin
      : "https://prepza.ai"

  function call(callback, value) {
    if (typeof callback === "function") {
      callback(value)
    }
  }

  function warnUnknown(options) {
    for (var name in options) {
      if (
        Object.prototype.hasOwnProperty.call(options, name) &&
        OPTIONS.indexOf(name) === -1
      ) {
        console.warn("Prepza.embed: unknown option " + name)
      }
    }
  }

  function embed(options) {
    var element =
      typeof options.element === "string"
        ? document.querySelector(options.element)
        : options.element

    if (!element) {
      throw new Error("Prepza.embed: no element " + options.element)
    }

    warnUnknown(options)
    var token = new URL(options.url).pathname.split("/").filter(Boolean).pop()
    var frame = document.createElement("iframe")
    frame.src =
      ORIGIN +
      "/embedded/" +
      encodeURIComponent(token) +
      "?origin=" +
      encodeURIComponent(window.location.origin) +
      (options.theme ? "&theme=" + encodeURIComponent(options.theme) : "")
    frame.title = options.title || "Interview"
    frame.style.cssText =
      "display:block;width:100%;border:0;height:" + MIN_HEIGHT + "px"

    // An iframe never says it failed to load: no "ready" in time is the failure.
    var timer = window.setTimeout(function () {
      call(options.onError, { code: "timeout" })
    }, READY_TIMEOUT_MS)

    function listen(event) {
      var data = event.data

      if (
        event.origin !== ORIGIN ||
        event.source !== frame.contentWindow ||
        !data ||
        data.source !== SOURCE
      ) {
        return
      }

      if (data.type === "resize") {
        if (typeof data.height === "number" && isFinite(data.height)) {
          frame.style.height = Math.max(data.height, MIN_HEIGHT) + "px"
        }
      } else if (data.type === "ready") {
        window.clearTimeout(timer)
        call(options.onReady)
      } else if (data.type === "started") {
        call(options.onStart)
      } else if (data.type === "finished") {
        call(options.onFinish, {
          candidateId:
            typeof data.candidateId === "string" ? data.candidateId : undefined,
        })
      } else if (data.type === "error") {
        call(options.onError, { code: String(data.code) })
      }
    }

    window.addEventListener("message", listen)
    element.appendChild(frame)

    return {
      destroy: function () {
        window.clearTimeout(timer)
        window.removeEventListener("message", listen)
        frame.remove()
      },
    }
  }

  window.Prepza = { version: VERSION, embed: embed }

  // A queued call that throws (a missing element) still reaches the page's console, after the
  // other queued calls ran.
  function rethrow(error) {
    window.setTimeout(function () {
      throw error
    })
  }

  // Calls the page made before this loaded.
  var queued = (existing && existing.q) || []

  for (var i = 0; i < queued.length; i++) {
    try {
      embed(queued[i])
    } catch (error) {
      rethrow(error)
    }
  }
})()
