// Search and tag filtering for the home page. No dependencies.
(function () {
  var list = document.getElementById("list");
  if (!list) return;
  var input = document.getElementById("q");
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var cards = Array.prototype.slice.call(list.querySelectorAll(".recipe-card"));
  var countEl = document.getElementById("count");
  var emptyEl = document.getElementById("empty");
  var params = new URLSearchParams(location.search);
  var state = { q: params.get("q") || "", tag: params.get("tag") || "all" };

  if (!chips.some(function (c) { return c.dataset.tag === state.tag; })) state.tag = "all";
  input.value = state.q;

  function apply() {
    var terms = state.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    var shown = 0;
    cards.forEach(function (card) {
      var tags = card.dataset.tags.split(" ");
      var hay = card.dataset.search;
      var ok = (state.tag === "all" || tags.indexOf(state.tag) !== -1) &&
        terms.every(function (t) { return hay.indexOf(t) !== -1; });
      card.hidden = !ok;
      if (ok) shown++;
    });
    chips.forEach(function (c) {
      var on = c.dataset.tag === state.tag;
      c.classList.toggle("is-active", on);
      c.setAttribute("aria-pressed", on ? "true" : "false");
    });
    countEl.textContent = shown + (shown === 1 ? " recipe" : " recipes");
    emptyEl.hidden = shown !== 0;
    var p = new URLSearchParams();
    if (state.q) p.set("q", state.q);
    if (state.tag !== "all") p.set("tag", state.tag);
    var qs = p.toString();
    history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
  }

  input.addEventListener("input", function () { state.q = input.value; apply(); });
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      state.tag = c.dataset.tag === state.tag ? "all" : c.dataset.tag;
      apply();
    });
  });
  apply();
})();
