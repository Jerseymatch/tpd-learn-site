// Click-to-load YouTube embeds: keeps pages fast until someone actually presses play.
document.addEventListener("click", function (ev) {
  var a = ev.target.closest && ev.target.closest("a[data-yt]");
  if (!a || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
  ev.preventDefault();
  var f = document.createElement("iframe");
  f.src = "https://www.youtube-nocookie.com/embed/" + a.getAttribute("data-yt") + "?autoplay=1&rel=0" + (a.getAttribute("data-start") ? "&start=" + a.getAttribute("data-start") : "");
  f.title = a.getAttribute("aria-label") || "YouTube video";
  f.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen";
  f.allowFullscreen = true;
  a.replaceChildren(f);
  a.removeAttribute("href");
});

// Next-class date: once it has passed, show the plain "see when the next class starts" link instead.
document.querySelectorAll("p.when[data-until]").forEach(function (p) {
  var until = new Date(p.getAttribute("data-until") + "T23:59:59");
  if (isNaN(until) || new Date() <= until) return;
  var a = document.createElement("a");
  a.href = p.getAttribute("data-href");
  a.innerHTML = p.getAttribute("data-fallback");
  p.replaceChildren(a);
});
