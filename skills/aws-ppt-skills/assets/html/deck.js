/* aws-ppt-skills HTML deck: slide navigation, slide list, laser, blank screen and the presenter view.
   One file serves both windows. The audience window shows the slides; "#presenter" in the address turns the
   same file into the presenter view (current slide, next slide, notes, timer). The two windows talk through
   postMessage, which also works for a deck opened from a disk (file://). */
(function () {
  "use strict";
  var W = 1280, H = 720;
  var root = document.documentElement, body = document.body;
  var deck = document.getElementById("deck");
  var slides = [].slice.call(deck.children).filter(function (n) { return n.classList.contains("slide"); });
  var total = slides.length;
  var deckId = deck.getAttribute("data-id") || "deck";
  var isPresenter = /^#presenter/.test(location.hash);
  var ko = (root.lang || "ko").slice(0, 2) === "ko";
  var L = ko ? {
    prev: "이전", next: "다음", list: "목록", presenter: "발표자 보기", full: "전체 화면", help: "도움말",
    popup: "발표자 보기 창이 열리지 않았습니다. 이 페이지의 팝업을 허용한 뒤 N을 다시 누르세요.",
    cur: "현재 슬라이드", nxt: "다음 슬라이드", notes: "발표자 노트", none: "이 슬라이드에는 노트가 없습니다.",
    end: "마지막 슬라이드입니다.", reset: "시간 재설정", blank: "화면 가리기", laser: "레이저", smaller: "글자 작게", larger: "글자 크게",
    slide: "슬라이드", keysTitle: "키보드 조작",
    keys: [["→  Space  PageDown", "다음 슬라이드"], ["←  PageUp", "이전 슬라이드"], ["Home  End", "처음, 마지막 슬라이드"],
      ["숫자 + Enter", "그 번호의 슬라이드로 이동"], ["N", "발표자 보기 창 열기(노트, 다음 슬라이드, 시간)"], ["F", "전체 화면"],
      ["G", "슬라이드 목록"], ["P", "레이저 포인터"], ["B", "화면 가리기"], ["?", "이 도움말"], ["Esc", "목록, 도움말, 레이저 닫기"]]
  } : {
    prev: "Previous", next: "Next", list: "Slides", presenter: "Presenter view", full: "Fullscreen", help: "Help",
    popup: "The presenter window did not open. Allow pop-ups for this page, then press N again.",
    cur: "Current slide", nxt: "Next slide", notes: "Speaker notes", none: "This slide has no notes.",
    end: "This is the last slide.", reset: "Reset timer", blank: "Blank screen", laser: "Laser", smaller: "Smaller text", larger: "Larger text",
    slide: "Slide", keysTitle: "Keyboard",
    keys: [["→  Space  PageDown", "Next slide"], ["←  PageUp", "Previous slide"], ["Home  End", "First and last slide"],
      ["number + Enter", "Go to that slide"], ["N", "Open the presenter window (notes, next slide, timer)"], ["F", "Fullscreen"],
      ["G", "Slide list"], ["P", "Laser pointer"], ["B", "Blank screen"], ["?", "This help"], ["Esc", "Close the list, the help and the laser"]]
  };

  var cur = -1, peer = isPresenter ? window.opener : null, digits = "", idleTimer = 0;
  var pv = null, pvCur = null, pvNext = null, pvNotes = null, pvCount = null, pvLaserBtn = null, pvBlankBtn = null;
  var grid = null, countEl = null, progress = null;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function button(label, fn, title) {
    var b = el("button", "", label);
    b.type = "button";
    if (title) { b.title = title; b.setAttribute("aria-label", title); }
    b.addEventListener("click", function (e) { e.stopPropagation(); fn(); b.blur(); });
    return b;
  }
  function clamp(i) { return Math.max(0, Math.min(total - 1, i)); }
  function cloneSlide(i) {
    var c = slides[i].cloneNode(true);
    c.removeAttribute("id");
    c.classList.add("active");
    c.setAttribute("aria-hidden", "true");
    [].forEach.call(c.querySelectorAll(".notes"), function (n) { n.remove(); });
    return c;
  }
  function send(msg) {
    msg.deck = deckId;
    try { if (peer && !peer.closed) peer.postMessage(msg, "*"); } catch (e) { /* the other window is gone */ }
  }
  function toast(text) {
    var t = document.getElementById("toast") || body.appendChild(Object.assign(el("div"), { id: "toast" }));
    t.textContent = text;
    t.style.display = "block";
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { t.style.display = "none"; }, 5000);
  }

  // ---- layout ----
  function fitStage(stage) {
    var s = stage.querySelector(".slide");
    if (!s) return;
    var k = Math.min(stage.clientWidth / W, stage.clientHeight / H);
    s.style.setProperty("--ts", k);
    s.style.setProperty("--tx", (stage.clientWidth - W * k) / 2 + "px");   // centered across, kept at the top
  }
  function fit() {
    deck.style.setProperty("--scale", Math.min(window.innerWidth / W, window.innerHeight / H));
    if (pv) { fitStage(pvCur); fitStage(pvNext); }
    if (grid && body.classList.contains("grid")) {
      [].forEach.call(grid.children, function (t) { t.firstChild.style.setProperty("--ts", t.clientWidth / W); });
    }
  }

  // ---- navigation ----
  function go(i, fromPeer) {
    i = clamp(i);
    if (i === cur) return;
    if (cur >= 0) slides[cur].classList.remove("active");
    cur = i;
    slides[cur].classList.add("active");
    try { history.replaceState(null, "", (isPresenter ? "#presenter-" : "#") + (cur + 1)); } catch (e) { /* file:// in some browsers */ }
    if (countEl) countEl.textContent = (cur + 1) + " / " + total;
    if (progress) progress.style.width = (total > 1 ? cur / (total - 1) * 100 : 100) + "%";
    if (pv) renderPresenter();
    if (!fromPeer) send({ type: "goto", index: cur });
  }
  function next() { go(cur + 1); }
  function prev() { go(cur - 1); }
  function fromHash() {
    var m = /(\d+)\s*$/.exec(location.hash);
    return m ? clamp(parseInt(m[1], 10) - 1) : 0;
  }

  // ---- overlays ----
  function toggleFull() {
    var d = document;
    if (d.fullscreenElement || d.webkitFullscreenElement) (d.exitFullscreen || d.webkitExitFullscreen).call(d);
    else (root.requestFullscreen || root.webkitRequestFullscreen || function () {}).call(root);
  }
  function buildGrid() {
    grid = el("div");
    grid.id = "grid";
    slides.forEach(function (s, i) {
      var t = el("div", "thumb");
      t.tabIndex = 0;
      t.setAttribute("role", "button");
      t.setAttribute("aria-label", L.slide + " " + (i + 1) + (s.getAttribute("data-title") ? ": " + s.getAttribute("data-title") : ""));
      t.appendChild(cloneSlide(i));
      t.appendChild(el("span", "no", String(i + 1)));
      var pick = function () { toggleGrid(false); go(i); };
      t.addEventListener("click", pick);
      t.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.stopPropagation(); pick(); } });
      grid.appendChild(t);
    });
    body.appendChild(grid);
  }
  function toggleGrid(on) {
    if (on === undefined) on = !body.classList.contains("grid");
    if (on && !grid) buildGrid();
    body.classList.toggle("grid", on);
    if (!on) return;
    [].forEach.call(grid.children, function (t, i) { t.classList.toggle("current", i === cur); });
    fit();
    grid.children[cur].scrollIntoView({ block: "center" });
    grid.children[cur].focus();
  }
  function toggleHelp(on) {
    var h = document.getElementById("help");
    if (!h) {
      h = el("div");
      h.id = "help";
      var panel = h.appendChild(el("div", "panel"));
      panel.appendChild(el("h2", "", L.keysTitle));
      var dl = panel.appendChild(el("dl"));
      L.keys.forEach(function (k) { dl.appendChild(el("dt", "", k[0])); dl.appendChild(el("dd", "", k[1])); });
      h.addEventListener("click", function () { toggleHelp(false); });
      body.appendChild(h);
    }
    body.classList.toggle("help", on === undefined ? !body.classList.contains("help") : on);
  }
  function laserDot() { return document.getElementById("laser") || body.appendChild(Object.assign(el("div"), { id: "laser" })); }
  function setLaser(on) {
    body.classList.toggle("laser", on);
    if (pvLaserBtn) pvLaserBtn.setAttribute("aria-pressed", String(on));
    if (!on) { laserDot().style.display = "none"; if (isPresenter) send({ type: "laser", on: false }); }
  }
  function setBlank(on, fromPeer) {
    body.classList.toggle("blank", on);
    if (pvBlankBtn) pvBlankBtn.setAttribute("aria-pressed", String(on));
    if (!fromPeer) send({ type: "blank", on: on });
  }
  // The dot is drawn where the pointer is over the slide. x and y are fractions of the slide, so the
  // presenter's preview and the audience window agree whatever their sizes are.
  function showLaser(box, x, y, on) {
    var dot = laserDot();
    if (!on || !box || x < 0 || x > 1 || y < 0 || y > 1) { dot.style.display = "none"; return; }
    var r = box.getBoundingClientRect();
    dot.style.left = r.left + r.width * x + "px";
    dot.style.top = r.top + r.height * y + "px";
    dot.style.display = "block";
  }
  function trackLaser(surface, box) {
    surface.addEventListener("mousemove", function (e) {
      if (!body.classList.contains("laser")) return;
      var r = box().getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      showLaser(box(), x, y, true);
      if (isPresenter) send({ type: "laser", on: true, x: x, y: y });
    });
    surface.addEventListener("mouseleave", function () {
      laserDot().style.display = "none";
      if (isPresenter) send({ type: "laser", on: false });
    });
  }

  // ---- presenter view ----
  function openPresenter() {
    if (peer && !peer.closed) { peer.focus(); return; }
    peer = window.open(location.href.split("#")[0] + "#presenter-" + (cur + 1), "deck-presenter-" + deckId, "width=1280,height=800");
    if (!peer) toast(L.popup);
  }
  function buildPresenter() {
    body.classList.add("presenter");
    pv = el("div");
    pv.id = "pv";
    var top = pv.appendChild(el("div", "top"));
    var timer = top.appendChild(el("span", "timer", "00:00"));
    var t0 = Date.now();
    top.appendChild(button(L.reset, function () { t0 = Date.now(); tick(); }));
    var clock = top.appendChild(el("span", "clock"));
    pvCount = top.appendChild(el("span", "count"));
    top.appendChild(el("span", "spacer"));
    top.appendChild(button("‹ " + L.prev, prev));
    top.appendChild(button(L.next + " ›", next));
    pvLaserBtn = top.appendChild(button(L.laser, function () { setLaser(!body.classList.contains("laser")); }));
    pvBlankBtn = top.appendChild(button(L.blank, function () { setBlank(!body.classList.contains("blank")); }));
    top.appendChild(button("A-", function () { notesSize(-2); }, L.smaller));
    top.appendChild(button("A+", function () { notesSize(2); }, L.larger));
    top.appendChild(button("?", function () { toggleHelp(); }, L.help));

    var a = pv.appendChild(el("div", "pane cur"));
    a.appendChild(el("div", "label", L.cur));
    pvCur = a.appendChild(el("div", "stage"));
    var b = pv.appendChild(el("div", "pane nxt"));
    b.appendChild(el("div", "label", L.nxt));
    pvNext = b.appendChild(el("div", "stage"));
    var c = pv.appendChild(el("div", "pane notes-pane"));
    c.appendChild(el("div", "label", L.notes));
    pvNotes = c.appendChild(el("div", "text"));
    body.appendChild(pv);
    trackLaser(pvCur, function () { return pvCur.querySelector(".slide"); });

    function two(n) { return (n < 10 ? "0" : "") + n; }
    function tick() {
      var s = Math.floor((Date.now() - t0) / 1000), h = Math.floor(s / 3600);
      timer.textContent = (h ? h + ":" : "") + two(Math.floor(s % 3600 / 60)) + ":" + two(s % 60);
      var d = new Date();
      clock.textContent = two(d.getHours()) + ":" + two(d.getMinutes());
    }
    tick();
    setInterval(tick, 500);
    notesSize(0);
  }
  function notesSize(step) {
    var size = 20;
    try { size = parseInt(localStorage.getItem("deck-notes-size"), 10) || 20; } catch (e) { /* storage blocked */ }
    size = Math.max(12, Math.min(44, size + step));
    try { localStorage.setItem("deck-notes-size", String(size)); } catch (e) { /* storage blocked */ }
    pvNotes.style.setProperty("--notes-size", size + "px");
  }
  function renderPresenter() {
    pvCur.textContent = "";
    pvCur.appendChild(cloneSlide(cur));
    pvNext.textContent = "";
    if (cur + 1 < total) pvNext.appendChild(cloneSlide(cur + 1));
    else pvNext.appendChild(el("div", "end", L.end));
    pvNotes.textContent = "";
    var notes = slides[cur].querySelector(".notes");
    if (notes && notes.children.length) {
      [].forEach.call(notes.children, function (p) { pvNotes.appendChild(el("p", "", p.textContent)); });
    } else {
      pvNotes.appendChild(el("p", "none", L.none));
    }
    pvNotes.scrollTop = 0;
    pvCount.textContent = (cur + 1) + " / " + total;
    fit();
  }

  // ---- messages between the two windows ----
  window.addEventListener("message", function (e) {
    var m = e.data;
    if (!m || m.deck !== deckId || e.source === window) return;
    if (m.type === "hello" && !isPresenter) {            // a presenter window (re)loaded: adopt it and send the state
      peer = e.source;
      send({ type: "goto", index: cur });
      send({ type: "blank", on: body.classList.contains("blank") });
    } else if (m.type === "goto" && typeof m.index === "number") {
      go(m.index, true);
    } else if (m.type === "blank") {
      setBlank(!!m.on, true);
    } else if (m.type === "laser" && !isPresenter) {
      showLaser(slides[cur], Number(m.x), Number(m.y), !!m.on);
    }
  });

  // ---- keys, pointer, touch ----
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    var k = e.key;
    if (/^[0-9]$/.test(k)) { digits += k; return; }
    if (k === "Enter" && digits) { go(parseInt(digits, 10) - 1); digits = ""; e.preventDefault(); return; }
    digits = "";
    if (k === "Escape") { toggleGrid(false); toggleHelp(false); setLaser(false); return; }
    if (body.classList.contains("grid") && k !== "g" && k !== "G") return;   // the list handles its own keys
    switch (k) {
      case "ArrowRight": case "ArrowDown": case "PageDown": case " ": case "Spacebar": case "Enter": next(); break;
      case "ArrowLeft": case "ArrowUp": case "PageUp": case "Backspace": prev(); break;
      case "Home": go(0); break;
      case "End": go(total - 1); break;
      case "n": case "N": if (!isPresenter) openPresenter(); break;
      case "f": case "F": toggleFull(); break;
      case "g": case "G": if (!isPresenter) toggleGrid(); break;
      case "p": case "P": setLaser(!body.classList.contains("laser")); break;
      case "b": case "B": case ".": setBlank(!body.classList.contains("blank")); break;
      case "?": case "h": case "H": toggleHelp(); break;
      default: return;
    }
    e.preventDefault();
  });
  var touchX = null;
  deck.addEventListener("touchstart", function (e) { touchX = e.touches.length === 1 ? e.touches[0].clientX : null; }, { passive: true });
  deck.addEventListener("touchend", function (e) {
    if (touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX;
    touchX = null;
    if (Math.abs(dx) > 50) { if (dx < 0) next(); else prev(); }
  });
  function wake() {
    body.classList.remove("idle");
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () { if (!body.classList.contains("laser")) body.classList.add("idle"); }, 2600);
  }
  window.addEventListener("resize", fit);
  window.addEventListener("hashchange", function () { if (/^#presenter/.test(location.hash) === isPresenter) go(fromHash(), false); });

  // ---- start ----
  if (isPresenter) {
    buildPresenter();
  } else {
    var bar = el("div");
    bar.id = "bar";
    bar.appendChild(button("‹", prev, L.prev));
    countEl = bar.appendChild(el("span", "count"));
    bar.appendChild(button("›", next, L.next));
    bar.appendChild(button(L.list, function () { toggleGrid(); }));
    bar.appendChild(button(L.presenter, openPresenter));
    bar.appendChild(button(L.full, toggleFull));
    bar.appendChild(button("?", function () { toggleHelp(); }, L.help));
    body.appendChild(bar);
    progress = body.appendChild(Object.assign(el("div"), { id: "progress" }));
    trackLaser(deck, function () { return slides[cur]; });
    ["mousemove", "mousedown", "touchstart", "keydown"].forEach(function (ev) { document.addEventListener(ev, wake, { passive: true }); });
    wake();
  }
  fit();
  go(fromHash(), true);
  if (isPresenter) send({ type: "hello" });
})();
