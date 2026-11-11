(() => {
  if (window.__festaMotion) {
    window.__festaMotion.scan();
    return;
  }
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  let scheduled = false;
  let lastPage = null;
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    }
  }, { threshold: 0.06, rootMargin: "0px 0px 36px 0px" });
  function scan() {
    scheduled = false;
    const markers = document.querySelectorAll("[data-festa-page]");
    const currentPage = markers.length ? markers[markers.length - 1].dataset.festaPage : null;
    if (currentPage && currentPage !== lastPage) {
      lastPage = currentPage;
      document.querySelector('[data-testid="stMain"]')?.scrollTo({top:0,behavior:"instant"});
    }
    document.querySelectorAll("[data-festa-animate]:not([data-festa-observed])").forEach((node) => {
      node.dataset.festaObserved = "true";
      if (reduced.matches) return;
      node.classList.add("festa-reveal-ready");
      observer.observe(node);
    });
    document.querySelectorAll("[data-festa-focus]:not([data-festa-focused])").forEach((node) => {
      node.dataset.festaFocused = "true";
      // Aguarda a conclusão do layout do formulário após a navegação.
      window.setTimeout(() => {
        if (!node.isConnected) return;
        node.scrollIntoView({ behavior: reduced.matches ? "instant" : "smooth", block: "start" });
        const input = node.closest('[data-testid="stVerticalBlock"]')?.querySelector("input,select,textarea");
        input?.focus({ preventScroll: true });
      }, 160);
    });
  }
  const mutations = new MutationObserver(() => {
    if (!scheduled) {
      scheduled = true;
      window.requestAnimationFrame(scan);
    }
  });
  mutations.observe(document.body, { childList: true, subtree: true });
  reduced.addEventListener("change", () => {
    if (reduced.matches) {
      document.querySelectorAll(".festa-reveal-ready").forEach((node) => node.classList.add("is-visible"));
      observer.disconnect();
    } else {
      document.querySelectorAll("[data-festa-observed]").forEach((node) => {
        delete node.dataset.festaObserved;
      });
      scan();
    }
  });
  window.__festaMotion = { scan };
  scan();
})();