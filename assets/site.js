// Click-to-load YouTube embeds: keeps pages fast until someone actually presses play.
document.addEventListener("click", function (ev) {
  var a = ev.target.closest && ev.target.closest("a[data-yt]");
  if (!a || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
  ev.preventDefault();
  var f = document.createElement("iframe");
  f.src = "https://www.youtube-nocookie.com/embed/" + a.getAttribute("data-yt") + "?autoplay=1&rel=0";
  f.title = a.getAttribute("aria-label") || "YouTube video";
  f.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen";
  f.allowFullscreen = true;
  a.replaceChildren(f);
  a.removeAttribute("href");
});
