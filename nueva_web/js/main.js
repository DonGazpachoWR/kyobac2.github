/*
 * main.js
 *
 * Small progressive enhancements for the Kyobac Labs website: the mobile
 * navigation toggle, the footer year, the reveal-on-scroll effect, the
 * pointer parallax of the image mosaics, the looping product videos
 * (home hero and MycoRelax bottle), starting each page at the top
 * shrinking the header logo on scroll, discouraging copying and the
 * "Clara" chat assistant.
 * Every page works without this file.
 *
 * Version: 0.8
 * Author: Adrian Berenguer-Agustí (I2SysBio-CSIC)
 * Date: 2026-10-11
 */
(function () {
  "use strict";

  /**
   * Wire the hamburger button to open and close the navigation panel.
   * @returns {void}
   */
  function setupNavigation() {
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.getElementById("site-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        const is_open = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!is_open));
        nav.classList.toggle("is-open", !is_open);
      });
      // Close the panel after choosing a link or pressing Escape.
      nav.addEventListener("click", function (event) {
        if (event.target.closest("a")) {
          toggle.setAttribute("aria-expanded", "false");
          nav.classList.remove("is-open");
        }
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          toggle.setAttribute("aria-expanded", "false");
          nav.classList.remove("is-open");
        }
      });
    }
  }

  /**
   * Write the current year into every element with class "js-year".
   * @returns {void}
   */
  function setYear() {
    const year = String(new Date().getFullYear());
    document.querySelectorAll(".js-year").forEach(function (node) {
      node.textContent = year;
    });
  }

  /**
   * Fade in elements with class "reveal" as they enter the viewport.
   * Falls back to showing everything when IntersectionObserver is absent.
   * @returns {void}
   */
  function setupReveal() {
    const items = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px" });
      items.forEach(function (item) {
        observer.observe(item);
      });
    } else {
      items.forEach(function (item) {
        item.classList.add("is-visible");
      });
    }
  }

  /**
   * Start every page at the top instead of restoring the previous scroll
   * position. Links with a fragment (#section) still jump to it.
   * @returns {void}
   */
  function setupScrollTop() {
    const GUARD_MS = 1000;
    const framed = window.self !== window.top;
    let user_moved = false;
    function toTop() {
      if (!window.location.hash && !user_moved) {
        // "instant" skips the smooth scrolling set in the stylesheet.
        window.scrollTo({ top: 0, left: 0, behavior: "instant" });
        // Inside a same-origin iframe that grows with its content, the
        // scroll belongs to the parent page; scrollIntoView moves it too.
        if (framed) {
          document.documentElement.scrollIntoView({
            block: "start",
            behavior: "instant"
          });
        }
      }
    }
    function markUserMove() {
      user_moved = true;
    }
    if ("scrollRestoration" in history) {
      history.scrollRestoration = "manual";
    }
    ["wheel", "touchstart", "keydown", "pointerdown"].forEach(function (name) {
      window.addEventListener(name, markUserMove, {
        once: true,
        passive: true
      });
    });
    toTop();
    // Until shortly after the page has loaded, undo any scroll the visitor
    // did not make (a position restored by the browser or a preview host).
    window.addEventListener("scroll", toTop, { passive: true });
    window.addEventListener("load", function () {
      toTop();
      window.setTimeout(function () {
        window.removeEventListener("scroll", toTop);
      }, GUARD_MS);
    });
    // Pages restored from the back-forward cache keep their scroll too.
    window.addEventListener("pageshow", function (event) {
      if (event.persisted) {
        user_moved = false;
        toTop();
      }
    });
  }

  /**
   * Discourage copying the site: block the context menu, image dragging
   * and the save (Ctrl/Cmd+S) and view-source (Ctrl/Cmd+U) shortcuts.
   * This is only a deterrent; the legal notice is what protects the
   * content.
   * @returns {void}
   */
  function setupCopyGuard() {
    const BLOCKED_KEYS = ["s", "u"];
    document.addEventListener("contextmenu", function (event) {
      event.preventDefault();
    });
    document.addEventListener("dragstart", function (event) {
      if (event.target instanceof HTMLImageElement) {
        event.preventDefault();
      }
    });
    document.addEventListener("keydown", function (event) {
      const key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && BLOCKED_KEYS.includes(key)) {
        event.preventDefault();
      }
    });
  }

  /**
   * Mark the header as scrolled once the page leaves the top, so the CSS
   * can shrink the logo to the K monogram alone.
   * @returns {void}
   */
  function setupHeaderScroll() {
    const SCROLL_LIMIT = 24;
    const header = document.querySelector(".site-header");
    if (header) {
      // Toggling one class is cheap enough to run on every scroll event.
      const update = function () {
        header.classList.toggle("is-scrolled", window.scrollY > SCROLL_LIMIT);
      };
      window.addEventListener("scroll", update, { passive: true });
      update();
    }
  }

  /**
   * Shift the mosaic images with the pointer, as on the BioStrata home
   * page. Each mosaic listens to its own section and receives the offset
   * through the --mx and --my CSS custom properties.
   * @returns {void}
   */
  function setupParallax() {
    const MAX_SHIFT = 14;
    const can_hover = window.matchMedia("(hover: hover)").matches;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (can_hover && !reduce) {
      document.querySelectorAll(".mosaic").forEach(function (mosaic) {
        const area = mosaic.closest("section") || mosaic;
        let frame = 0;
        area.addEventListener("mousemove", function (event) {
          cancelAnimationFrame(frame);
          frame = requestAnimationFrame(function () {
            const x = (event.clientX / window.innerWidth - 0.5) * 2 * MAX_SHIFT;
            const y = (event.clientY / window.innerHeight - 0.5) * 2 * MAX_SHIFT;
            mosaic.style.setProperty("--mx", x.toFixed(1) + "px");
            mosaic.style.setProperty("--my", y.toFixed(1) + "px");
          });
        });
      });
    }
  }

  /**
   * Play the looping product videos (the home hero's confocal dive and
   * the MycoRelax bottle; specs in animaciones/) only while they are on
   * screen. With reduced motion they never play and the poster frame
   * stays.
   * @returns {void}
   */
  function setupLoopVideos() {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduce && "IntersectionObserver" in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            // Autoplay can be refused (e.g. data saver); the poster stays.
            entry.target.play().catch(function () {});
          } else {
            entry.target.pause();
          }
        });
      });
      document.querySelectorAll("video.js-loop-video").forEach(function (video) {
        observer.observe(video);
      });
    }
  }

  /**
   * Run Clara, the chat assistant built by _src/build.py. Questions go to
   * the Cloudflare Worker named in data-endpoint, which answers only from
   * the website content. The conversation lives in memory: nothing is
   * stored in the browser. Speech input (SpeechRecognition) and output
   * (speechSynthesis) are added only when the browser supports them;
   * recognition runs on the device when possible and otherwise, after a
   * one-time notice, on the browser vendor's servers.
   * @returns {void}
   */
  function setupAssistant() {
    const root = document.querySelector(".assistant");
    if (root && window.fetch) {
      startAssistant(root);
    }
  }

  /**
   * Wire the controls of the assistant widget (see setupAssistant).
   * @param {HTMLElement} root The ".assistant" element.
   * @returns {void}
   */
  function startAssistant(root) {
    // Messages sent to the Worker, and the longest question accepted.
    const MAX_HISTORY = 8;
    const MAX_CHARS = 600;
    // Milliseconds to wait for an answer before giving up.
    const TIMEOUT_MS = 25000;
    const LANG = "es-ES";
    const endpoint = root.dataset.endpoint;
    const contact = root.dataset.contact;
    const launcher = root.querySelector(".assistant-launcher");
    const panel = root.querySelector(".assistant-panel");
    const log = root.querySelector(".assistant-log");
    const form = root.querySelector(".assistant-form");
    const input = root.querySelector("#assistant-input");
    const send_button = root.querySelector(".assistant-send");
    const close_button = root.querySelector(".js-assistant-close");
    const mic_button = root.querySelector(".js-assistant-mic");
    const speak_button = root.querySelector(".js-assistant-speak");
    const Recognition = window.SpeechRecognition
      || window.webkitSpeechRecognition;
    const synth = window.speechSynthesis;
    const history = [];
    let busy = false;
    let speaking_on = false;
    let voice = null;
    let recognizer = null;
    let listening = false;
    let process_locally = false;
    let cloud_notice_shown = false;

    /**
     * Append one message bubble to the conversation log. Text is set with
     * textContent, so answers can never inject markup.
     * @param {string} text Message text.
     * @param {string} kind "user", "bot" or "note".
     * @returns {HTMLElement} The new bubble.
     */
    function addMessage(text, kind) {
      const bubble = document.createElement("p");
      bubble.className = "assistant-msg assistant-msg--" + kind;
      bubble.textContent = text;
      log.appendChild(bubble);
      log.scrollTop = log.scrollHeight;
      return bubble;
    }

    /**
     * Pick the best Spanish voice once the browser has loaded its list.
     * @returns {void}
     */
    function chooseVoice() {
      const voices = synth.getVoices();
      voice = voices.find(function (item) { return item.lang === LANG; })
        || voices.find(function (item) { return /^es/i.test(item.lang); })
        || null;
    }

    /**
     * Read a text aloud, one sentence per utterance: some Chrome voices
     * stop silently after about 15 seconds of continuous speech.
     * @param {string} text Text to read.
     * @returns {void}
     */
    function speak(text) {
      if (synth && speaking_on) {
        synth.cancel();
        const sentences = text.match(/[^.!?¿¡]+[.!?]*|[¿¡][^?!]*[?!]/g)
          || [text];
        sentences.forEach(function (sentence) {
          if (sentence.trim()) {
            const utterance = new SpeechSynthesisUtterance(sentence.trim());
            utterance.lang = LANG;
            if (voice) {
              utterance.voice = voice;
            }
            synth.speak(utterance);
          }
        });
      }
    }

    /**
     * Turn reading aloud on or off. Called from a click, which also
     * unlocks speech on iOS, where speak() needs a user gesture.
     * @returns {void}
     */
    function toggleSpeaking() {
      speaking_on = !speaking_on;
      speak_button.setAttribute("aria-pressed", String(speaking_on));
      if (speaking_on) {
        speak("De acuerdo, leeré mis respuestas en voz alta.");
      } else {
        synth.cancel();
      }
    }

    /**
     * Enable or disable the form while an answer is on its way.
     * @param {boolean} state True while waiting for the Worker.
     * @returns {void}
     */
    function setBusy(state) {
      busy = state;
      send_button.disabled = state;
      log.setAttribute("aria-busy", String(state));
    }

    /**
     * Send the question to the Worker and show Clara's answer.
     * @param {string} question Visitor's question.
     * @returns {Promise<void>} Resolves when the answer (or an error
     *     notice) is shown.
     */
    async function ask(question) {
      const text = question.trim().slice(0, MAX_CHARS);
      if (text && !busy) {
        await answer(text);
      }
    }

    /**
     * Show a question, wait for the Worker and show Clara's answer, or a
     * contact fallback if the Worker cannot answer.
     * @param {string} text Non-empty, trimmed question.
     * @returns {Promise<void>} Resolves when the answer is shown.
     */
    async function answer(text) {
      addMessage(text, "user");
      history.push({ role: "user", content: text });
      setBusy(true);
      const typing = addMessage("Clara está escribiendo…", "typing");
      const controller = new AbortController();
      const timer = window.setTimeout(function () {
        controller.abort();
      }, TIMEOUT_MS);
      let reply = "";
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: history.slice(-MAX_HISTORY) }),
          signal: controller.signal
        });
        const data = await response.json();
        reply = response.ok && typeof data.reply === "string"
          ? data.reply
          : "";
        if (response.status === 429) {
          reply = "Has enviado muchas preguntas seguidas. Espera un minuto "
            + "y vuelve a intentarlo, por favor.";
        }
      } catch (error) {
        reply = "";
      }
      window.clearTimeout(timer);
      typing.remove();
      if (reply) {
        history.push({ role: "assistant", content: reply });
        addMessage(reply, "bot");
        speak(reply);
      } else {
        // Drop the unanswered question so the next request stays valid.
        history.pop();
        addMessage("Lo siento, ahora no puedo responder. Inténtalo más "
          + "tarde o escríbenos a " + contact + ".", "note");
      }
      setBusy(false);
    }

    /**
     * Decide whether speech can be recognised on the device (Chrome 139+
     * with the Spanish model installed). Any failure means "no".
     * @returns {Promise<void>} Resolves once process_locally is set.
     */
    async function checkLocalRecognition() {
      try {
        if (typeof Recognition.available === "function") {
          const status = await Recognition.available({
            langs: [LANG],
            processLocally: true
          });
          process_locally = status === "available";
        }
      } catch (error) {
        process_locally = false;
      }
    }

    /**
     * Start or stop listening. Before the first cloud transcription the
     * visitor is told where the audio goes and must press again.
     * @returns {void}
     */
    function toggleListening() {
      if (listening) {
        recognizer.stop();
      } else if (!process_locally && !cloud_notice_shown) {
        cloud_notice_shown = true;
        addMessage("Para convertir tu voz en texto, tu navegador puede "
          + "enviar el audio a los servidores de su proveedor (por ejemplo, "
          + "Google o Apple). Kyobac Labs no recibe ni guarda el audio. "
          + "Si estás de acuerdo, pulsa de nuevo el micrófono.", "note");
      } else {
        recognizer = new Recognition();
        recognizer.lang = LANG;
        recognizer.interimResults = true;
        recognizer.maxAlternatives = 1;
        if (process_locally) {
          recognizer.processLocally = true;
        }
        recognizer.onstart = function () {
          listening = true;
          mic_button.setAttribute("aria-pressed", "true");
          mic_button.setAttribute("aria-label", "Dejar de escuchar");
        };
        recognizer.onresult = function (event) {
          const transcript = Array.from(event.results).map(function (item) {
            return item[0].transcript;
          }).join("");
          input.value = transcript;
          if (event.results[event.results.length - 1].isFinal) {
            input.value = "";
            ask(transcript);
          }
        };
        recognizer.onerror = function (event) {
          if (event.error === "not-allowed"
              || event.error === "service-not-allowed") {
            addMessage("No tengo permiso para usar el micrófono. Puedes "
              + "escribir tu pregunta.", "note");
          }
        };
        recognizer.onend = function () {
          listening = false;
          mic_button.setAttribute("aria-pressed", "false");
          mic_button.setAttribute("aria-label", "Hablar");
        };
        recognizer.start();
      }
    }

    /**
     * Show or hide the chat panel, moving the focus accordingly.
     * @param {boolean} open True to open the panel.
     * @returns {void}
     */
    function setOpen(open) {
      panel.hidden = !open;
      launcher.setAttribute("aria-expanded", String(open));
      root.classList.toggle("is-open", open);
      if (open) {
        input.focus();
      } else {
        if (synth) {
          synth.cancel();
        }
        if (listening) {
          recognizer.abort();
        }
        launcher.focus();
      }
    }

    launcher.addEventListener("click", function () {
      setOpen(panel.hidden);
    });
    close_button.addEventListener("click", function () {
      setOpen(false);
    });
    panel.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    });
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const question = input.value;
      input.value = "";
      ask(question);
    });
    // Enter sends; Shift+Enter adds a new line.
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
    if (synth && window.SpeechSynthesisUtterance) {
      // The voice list loads asynchronously, notably in Chrome.
      chooseVoice();
      synth.onvoiceschanged = chooseVoice;
      speak_button.hidden = false;
      speak_button.addEventListener("click", toggleSpeaking);
    }
    if (Recognition) {
      checkLocalRecognition();
      mic_button.hidden = false;
      mic_button.addEventListener("click", toggleListening);
    }
  }

  setupScrollTop();
  setupCopyGuard();
  setupHeaderScroll();
  setupNavigation();
  setYear();
  setupReveal();
  setupParallax();
  setupLoopVideos();
  setupAssistant();
})();
