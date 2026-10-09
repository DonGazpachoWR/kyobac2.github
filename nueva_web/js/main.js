/*
 * main.js
 *
 * Small progressive enhancements for the Kyobac website: the mobile
 * navigation toggle, the footer year and the reveal-on-scroll effect.
 * Every page works without this file.
 *
 * Version: 0.1
 * Author: Adrian Berenguer-Agustí (I2SysBio-CSIC)
 * Date: 2026-10-09
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

  setupNavigation();
  setYear();
  setupReveal();
})();
