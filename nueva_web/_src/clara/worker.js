/*
 * worker.js
 *
 * Cloudflare Worker behind "Clara", the chat assistant of the Kyobac Labs
 * website. GitHub Pages is static, so the browser cannot hold any secret;
 * this Worker receives the conversation, adds Clara's instructions and the
 * knowledge base (both plain-text modules generated or kept in this
 * folder) and asks a Workers AI model for the reply. Nothing is stored or
 * logged: each request carries the whole (short) conversation.
 *
 * Endpoint: POST /chat  {"messages": [{"role": "user", "content": "..."}]}
 * Answer:   200 {"reply": "..."}  or  4xx/5xx {"error": "<code>"}
 *
 * Version: 1.0
 * Author: Adrian Berenguer-Agustí (I2SysBio-CSIC)
 * Date: 2026-10-10
 */
import INSTRUCTIONS from "./instrucciones.txt";
import KNOWLEDGE from "./conocimiento.txt";

// Clara's full system prompt: behaviour rules first, then the website text.
const SYSTEM_PROMPT = INSTRUCTIONS.trim()
  + "\n\nBASE DE CONOCIMIENTO (contenido de la web de Kyobac Labs)\n\n"
  + KNOWLEDGE.trim();
// Messages kept from the end of the conversation (user and assistant).
const MAX_MESSAGES = 8;
// Longest accepted visitor message, in characters.
const MAX_USER_CHARS = 600;
// Longest accepted earlier assistant message, in characters.
const MAX_ASSISTANT_CHARS = 1500;
// Largest accepted request body, in bytes.
const MAX_BODY_BYTES = 16000;
// Generation settings: short, focused answers.
const MAX_OUTPUT_TOKENS = 350;
const TEMPERATURE = 0.2;

/**
 * Build the CORS headers for an allowed origin.
 * @param {string} origin Origin of the request, already checked.
 * @returns {Object<string, string>} Headers to add to the response.
 */
function corsHeaders(origin) {
  const result = {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin"
  };
  return result;
}

/**
 * Build a JSON response.
 * @param {Object} body Payload to serialise.
 * @param {number} status HTTP status code.
 * @param {Object<string, string>} headers Extra headers (CORS).
 * @returns {Response} The response.
 */
function jsonResponse(body, status, headers) {
  const result = new Response(JSON.stringify(body), {
    status: status,
    headers: Object.assign({
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    }, headers)
  });
  return result;
}

/**
 * Check and trim the conversation sent by the browser.
 * @param {*} payload Parsed request body.
 * @returns {Array<{role: string, content: string}>|null} The last
 *     MAX_MESSAGES messages, or null if the payload is not valid.
 */
function cleanMessages(payload) {
  let result = null;
  const messages = payload && Array.isArray(payload.messages)
    ? payload.messages.slice(-MAX_MESSAGES)
    : [];
  const is_valid = messages.length > 0 && messages.every(function (msg) {
    const limit = msg && msg.role === "user"
      ? MAX_USER_CHARS
      : MAX_ASSISTANT_CHARS;
    return msg
      && (msg.role === "user" || msg.role === "assistant")
      && typeof msg.content === "string"
      && msg.content.trim().length > 0
      && msg.content.length <= limit;
  });
  if (is_valid && messages[messages.length - 1].role === "user") {
    result = messages.map(function (msg) {
      return { role: msg.role, content: msg.content.trim() };
    });
  }
  return result;
}

/**
 * Pull the generated text out of a Workers AI answer. Older models
 * return {response}, OpenAI-compatible ones return {choices}.
 * @param {*} answer Value returned by env.AI.run.
 * @returns {string} The reply text, or "" if none was found.
 */
function extractReply(answer) {
  let result = "";
  if (answer && typeof answer.response === "string") {
    result = answer.response;
  } else if (answer && Array.isArray(answer.choices) && answer.choices[0]
             && answer.choices[0].message) {
    result = String(answer.choices[0].message.content || "");
  }
  // Some models emit their reasoning between <think> tags; drop it.
  result = result.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
  return result;
}

/**
 * Answer one chat request.
 * @param {Request} request Incoming POST request.
 * @param {Object} env Worker bindings: AI, MODEL and, optionally,
 *     RATE_LIMITER.
 * @param {Object<string, string>} headers CORS headers for the answer.
 * @returns {Promise<Response>} JSON response with the reply or an error.
 */
async function handleChat(request, env, headers) {
  let response = null;
  const client_ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const limit = env.RATE_LIMITER
    ? await env.RATE_LIMITER.limit({ key: client_ip })
    : { success: true };
  const body = await request.text();
  let payload = null;
  if (body.length <= MAX_BODY_BYTES) {
    try {
      payload = JSON.parse(body);
    } catch (error) {
      payload = null;
    }
  }
  const messages = cleanMessages(payload);
  if (!limit.success) {
    response = jsonResponse({ error: "rate_limited" }, 429, headers);
  } else if (messages === null) {
    response = jsonResponse({ error: "bad_request" }, 400, headers);
  } else {
    try {
      const answer = await env.AI.run(env.MODEL, {
        messages: [{ role: "system", content: SYSTEM_PROMPT }]
          .concat(messages),
        max_tokens: MAX_OUTPUT_TOKENS,
        temperature: TEMPERATURE
      });
      const reply = extractReply(answer);
      response = reply
        ? jsonResponse({ reply: reply }, 200, headers)
        : jsonResponse({ error: "empty_reply" }, 502, headers);
    } catch (error) {
      // Workers AI fails when the free daily allowance is used up or the
      // model is busy; the browser shows a contact fallback either way.
      // The error text is not logged because it may echo the prompt.
      response = jsonResponse({ error: "model_unavailable" }, 503, headers);
    }
  }
  return response;
}

export default {
  /**
   * Route a request: CORS preflight, chat, or rejection.
   * @param {Request} request Incoming request.
   * @param {Object} env Worker bindings and variables (ALLOWED_ORIGINS
   *     is a comma-separated list of origins allowed to call the API).
   * @returns {Promise<Response>} The response.
   */
  async fetch(request, env) {
    let response = null;
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const allowed = String(env.ALLOWED_ORIGINS || "")
      .split(",")
      .map(function (item) { return item.trim(); })
      .filter(Boolean);
    const is_allowed = allowed.includes(origin);
    const headers = is_allowed ? corsHeaders(origin) : {};
    if (url.pathname !== "/chat") {
      response = jsonResponse({ error: "not_found" }, 404, headers);
    } else if (!is_allowed) {
      response = jsonResponse({ error: "forbidden_origin" }, 403, {});
    } else if (request.method === "OPTIONS") {
      response = new Response(null, { status: 204, headers: headers });
    } else if (request.method === "POST") {
      response = await handleChat(request, env, headers);
    } else {
      response = jsonResponse({ error: "method_not_allowed" }, 405, headers);
    }
    return response;
  }
};
